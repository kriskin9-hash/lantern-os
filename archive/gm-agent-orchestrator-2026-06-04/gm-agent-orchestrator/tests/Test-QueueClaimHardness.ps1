[CmdletBinding()]
param(
    [string]$Root = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Root)) {
    $scriptDir = if (-not [string]::IsNullOrWhiteSpace($PSScriptRoot)) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Path }
    $Root = (Resolve-Path (Join-Path $scriptDir "..")).Path
}
else {
    $Root = (Resolve-Path $Root).Path
}

$claimScript = Join-Path $Root "scripts\Claim-OrchestratorQueueTask.ps1"
$moveScript = Join-Path $Root "scripts\Move-OrchestratorTask.ps1"
foreach ($script in @($claimScript, $moveScript)) {
    if (-not (Test-Path -LiteralPath $script -PathType Leaf)) {
        throw "Required queue script was not found: $script"
    }
}

$tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("orch-queue-claim-hardness-{0}" -f [Guid]::NewGuid().ToString("N"))

function New-TestRoot {
    param([string]$Path)

    foreach ($relativePath in @(
        "tasks\queue",
        "tasks\active",
        "tasks\done",
        "tasks\failed",
        "tasks\hold",
        "scripts",
        "config\queue-strategies",
        "reports\queue-movements"
    )) {
        New-Item -ItemType Directory -Force -Path (Join-Path $Path $relativePath) | Out-Null
    }

    Copy-Item -LiteralPath $moveScript -Destination (Join-Path $Path "scripts\Move-OrchestratorTask.ps1") -Force

    @'
{
  "name": "default.cost-optimized",
  "costMode": "minimize_paid_tokens",
  "movementPolicy": {
    "defaultReason": "queue strategy movement",
    "forbidOverwrite": true,
    "forbidPathTraversal": true
  }
}
'@ | Set-Content -LiteralPath (Join-Path $Path "config\queue-strategies\default.cost-optimized.json") -Encoding UTF8
}

function New-TaskFile {
    param(
        [string]$Name,
        [string]$Text
    )

    $path = Join-Path $tempRoot ("tasks\queue\{0}" -f $Name)
    $Text | Set-Content -LiteralPath $path -Encoding UTF8
    return $path
}

function Invoke-Claim {
    param([string[]]$Arguments)

    $previousErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $output = & powershell -NoProfile -ExecutionPolicy Bypass -File $claimScript @Arguments 2>&1
        $exitCode = $LASTEXITCODE
        if ($null -eq $exitCode) { $exitCode = 0 }
        return [pscustomobject]@{
            exitCode = [int]$exitCode
            output = ($output | ForEach-Object { $_.ToString() }) -join "`n"
        }
    }
    catch {
        return [pscustomobject]@{
            exitCode = 1
            output = $_.Exception.Message
        }
    }
    finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }
}

function Convert-ClaimOutput {
    param([string]$Output)

    $trimmed = $Output.Trim()
    if (-not $trimmed.StartsWith("{")) {
        throw "Expected JSON object from claim selector. Actual output: $Output"
    }
    return $trimmed | ConvertFrom-Json -ErrorAction Stop
}

function Assert-Count {
    param(
        [string]$State,
        [int]$Expected,
        [string]$Message
    )

    $dir = Join-Path $tempRoot ("tasks\{0}" -f $State)
    $count = @(Get-ChildItem -LiteralPath $dir -File -Filter "*.md" -ErrorAction SilentlyContinue).Count
    if ($count -ne $Expected) {
        throw "$Message Expected $Expected in $State, got $count."
    }
}

$headlessCapabilities = "implementation,recovery"

try {
    New-TestRoot -Path $tempRoot

    $empty = Invoke-Claim -Arguments @("-Root", $tempRoot, "-SlotName", "headless", "-Role", "implementation", "-Capabilities", $headlessCapabilities)
    if ($empty.exitCode -ne 0) { throw "Empty queue claim failed: $($empty.output)" }
    $emptyJson = Convert-ClaimOutput -Output $empty.output
    if (-not $emptyJson.ok -or $emptyJson.state -ne "no_queued_tasks") { throw "Expected no_queued_tasks, got: $($empty.output)" }

    New-TaskFile -Name "p2-dashboard-polish.md" -Text @'
# Dashboard polish

Priority: P2
Owner: review-helper

This is a cosmetic dashboard item with no recovery, queue, shell, facilitator, or headless work.
'@ | Out-Null

    $notCompatible = Invoke-Claim -Arguments @("-Root", $tempRoot, "-SlotName", "reviewer", "-Role", "review", "-Capabilities", "review")
    if ($notCompatible.exitCode -ne 0) { throw "No-compatible claim failed unexpectedly: $($notCompatible.output)" }
    $notCompatibleJson = Convert-ClaimOutput -Output $notCompatible.output
    if (-not $notCompatibleJson.ok -or $notCompatibleJson.state -ne "claimed") { throw "Expected claimed, got: $($notCompatible.output)" }
    Assert-Count -State "queue" -Expected 0 -Message "Compatible claim must remove queue task."
    Assert-Count -State "active" -Expected 1 -Message "Compatible claim must create active work."

    # Remove the active task from the previous successful claim test so the next dry-run test starts with an empty active directory.
    Remove-Item -LiteralPath (Join-Path $tempRoot "tasks\active\reviewer__p2-dashboard-polish.md") -Force

    New-TaskFile -Name "p0-196-disaster-recovery.md" -Text @'
# P0 disaster recovery

Priority: P0
Issue: #196

Recover headless local-shell queue claim behavior for disaster recovery.
'@ | Out-Null

    $dryRun = Invoke-Claim -Arguments @("-Root", $tempRoot, "-SlotName", "headless", "-Role", "implementation", "-Capabilities", $headlessCapabilities, "-DryRun")
    if ($dryRun.exitCode -ne 0) { throw "Dry-run claim failed: $($dryRun.output)" }
    $dryRunJson = Convert-ClaimOutput -Output $dryRun.output
    if (-not $dryRunJson.ok -or $dryRunJson.state -ne "claim_dry_run") { throw "Expected claim_dry_run, got: $($dryRun.output)" }
    if ($dryRunJson.selectedTask.name -ne "p0-196-disaster-recovery.md") { throw "Unexpected dry-run selected task: $($dryRunJson.selectedTask.name)" }
    Assert-Count -State "queue" -Expected 1 -Message "Dry-run claim must preserve queue."
    Assert-Count -State "active" -Expected 0 -Message "Dry-run claim must not create active work."

    $claim = Invoke-Claim -Arguments @("-Root", $tempRoot, "-SlotName", "headless", "-Role", "implementation", "-Capabilities", $headlessCapabilities)
    if ($claim.exitCode -ne 0) { throw "Real claim failed: $($claim.output)" }
    $claimJson = Convert-ClaimOutput -Output $claim.output
    if (-not $claimJson.ok -or $claimJson.state -ne "claimed") { throw "Expected claimed, got: $($claim.output)" }
    if ($claimJson.activePath -ne "tasks\active\headless__p0-196-disaster-recovery.md") { throw "Unexpected activePath: $($claimJson.activePath)" }
    if (-not (Test-Path -LiteralPath (Join-Path $tempRoot "tasks\active\headless__p0-196-disaster-recovery.md") -PathType Leaf)) { throw "Claim did not create active task." }
    Assert-Count -State "queue" -Expected 0 -Message "Claim must remove queued source."
    Assert-Count -State "active" -Expected 1 -Message "Claim must create exactly one active task."

    $auditFiles = @(Get-ChildItem -LiteralPath (Join-Path $tempRoot "reports\queue-movements") -Filter "*.jsonl" -File -ErrorAction SilentlyContinue)
    if ($auditFiles.Count -ne 1) { throw "Expected one queue movement audit file after claim, got $($auditFiles.Count)." }
    $auditRecords = @(Get-Content -LiteralPath $auditFiles[0].FullName | ForEach-Object { $_ | ConvertFrom-Json -ErrorAction Stop })
    $audit = $auditRecords | Where-Object { $_.slot -eq "headless" } | Select-Object -First 1
    if ($null -eq $audit -or $audit.from -ne "queue" -or $audit.to -ne "active" -or $audit.slot -ne "headless") { throw "Claim audit did not capture queue->active headless movement." }

    Move-Item -LiteralPath (Join-Path $tempRoot "tasks\active\headless__p0-196-disaster-recovery.md") -Destination (Join-Path $tempRoot "tasks\done\p0-196-disaster-recovery.md")

    New-TaskFile -Name "p0-conflict.md" -Text @'
# P0 conflict

Priority: P0

Recover headless queue behavior.
'@ | Out-Null
    "# existing active conflict" | Set-Content -LiteralPath (Join-Path $tempRoot "tasks\active\headless__p0-conflict.md") -Encoding UTF8

    $conflict = Invoke-Claim -Arguments @("-Root", $tempRoot, "-SlotName", "headless", "-Role", "implementation", "-Capabilities", $headlessCapabilities)
    if ($conflict.exitCode -ne 0) { throw "Conflict should return structured JSON, not process failure: $($conflict.output)" }
    $conflictJson = Convert-ClaimOutput -Output $conflict.output
    if ($conflictJson.ok -ne $false -or $conflictJson.state -ne "error") { throw "Expected structured error on destination conflict, got: $($conflict.output)" }
    if ($conflictJson.error -notmatch "Destination already exists") { throw "Expected destination conflict error, got: $($conflictJson.error)" }
    if (-not (Test-Path -LiteralPath (Join-Path $tempRoot "tasks\queue\p0-conflict.md") -PathType Leaf)) { throw "Conflict must leave queued source in place." }

    Remove-Item -LiteralPath (Join-Path $tempRoot "tasks\queue\p0-conflict.md") -Force
    Remove-Item -LiteralPath (Join-Path $tempRoot "tasks\active\headless__p0-conflict.md") -Force

    New-TaskFile -Name "p0-unsafe..name.md" -Text @'
# P0 unsafe name

Priority: P0

Recover headless queue behavior.
'@ | Out-Null

    $unsafe = Invoke-Claim -Arguments @("-Root", $tempRoot, "-SlotName", "headless", "-Role", "implementation", "-Capabilities", $headlessCapabilities)
    if ($unsafe.exitCode -ne 0) { throw "Unsafe name should return structured JSON, not process failure: $($unsafe.output)" }
    $unsafeJson = Convert-ClaimOutput -Output $unsafe.output
    if ($unsafeJson.ok -ne $false -or $unsafeJson.state -ne "error") { throw "Expected structured error on unsafe task name, got: $($unsafe.output)" }
    if ($unsafeJson.error -notmatch "TaskName must be a file name") { throw "Expected unsafe task name error, got: $($unsafeJson.error)" }
    if (-not (Test-Path -LiteralPath (Join-Path $tempRoot "tasks\queue\p0-unsafe..name.md") -PathType Leaf)) { throw "Unsafe claim must leave queued source in place." }

    Remove-Item -LiteralPath (Join-Path $tempRoot "tasks\queue\p0-unsafe..name.md") -Force

    New-TaskFile -Name "p1-recovery.md" -Text @'
# P1 recovery

Priority: P1

Recovery-related but not urgent.
'@ | Out-Null

    $urgentOnly = Invoke-Claim -Arguments @("-Root", $tempRoot, "-SlotName", "headless", "-Role", "implementation", "-Capabilities", $headlessCapabilities, "-UrgentOnly")
    if ($urgentOnly.exitCode -ne 0) { throw "Urgent-only claim failed unexpectedly: $($urgentOnly.output)" }
    $urgentOnlyJson = Convert-ClaimOutput -Output $urgentOnly.output
    if (-not $urgentOnlyJson.ok -or $urgentOnlyJson.state -ne "no_urgent_task") { throw "Expected no_urgent_task, got: $($urgentOnly.output)" }
    Assert-Count -State "queue" -Expected 1 -Message "Urgent-only no-op must preserve queue."
    Assert-Count -State "active" -Expected 0 -Message "Urgent-only no-op must not create active work."

    Write-Host "Queue claim hardness tests passed."
}
finally {
    Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
}

