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

$startSlotScript = Join-Path $Root "scripts\Start-AgentSlot.ps1"
$claimScript = Join-Path $Root "scripts\Claim-OrchestratorQueueTask.ps1"
$moveScript = Join-Path $Root "scripts\Move-OrchestratorTask.ps1"
$contractPath = Join-Path $Root "docs\agent-contract.md"

foreach ($path in @($startSlotScript, $claimScript, $moveScript, $contractPath)) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Required E2E dependency was not found: $path"
    }
}

function ConvertTo-Base64Json {
    param([Parameter(Mandatory = $true)]$Value)

    $json = $Value | ConvertTo-Json -Depth 30 -Compress
    return [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($json))
}

function New-PipelineRoot {
    $path = Join-Path ([System.IO.Path]::GetTempPath()) ("orch-work-pipeline-e2e-{0}" -f [Guid]::NewGuid().ToString("N"))

    foreach ($relativePath in @(
        "tasks\queue",
        "tasks\active",
        "tasks\done",
        "tasks\failed",
        "tasks\hold",
        "scripts",
        "docs",
        "logs",
        "locks",
        "status",
        "config\queue-strategies",
        "reports\queue-movements",
        "worktrees\headless-e2e"
    )) {
        New-Item -ItemType Directory -Force -Path (Join-Path $path $relativePath) | Out-Null
    }

    Copy-Item -LiteralPath $claimScript -Destination (Join-Path $path "scripts\Claim-OrchestratorQueueTask.ps1") -Force
    Copy-Item -LiteralPath $moveScript -Destination (Join-Path $path "scripts\Move-OrchestratorTask.ps1") -Force
    Copy-Item -LiteralPath $contractPath -Destination (Join-Path $path "docs\agent-contract.md") -Force

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
'@ | Set-Content -LiteralPath (Join-Path $path "config\queue-strategies\default.cost-optimized.json") -Encoding UTF8

    @'
[CmdletBinding()]
param(
    [ValidateSet("pass", "fail")]
    [string]$Mode = "pass",
    [string]$Prompt = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath "TASK_QUEUE.md" -PathType Leaf)) { throw "Fake worker did not receive TASK_QUEUE.md" }
if (-not (Test-Path -LiteralPath "AGENT_RESUME.md" -PathType Leaf)) { throw "Fake worker did not receive AGENT_RESUME.md" }

Add-Content -LiteralPath "AGENT_LOG.md" -Value ("Fake worker mode={0}" -f $Mode) -Encoding UTF8
Add-Content -LiteralPath "AGENT_LOG.md" -Value ("Prompt received={0}" -f (-not [string]::IsNullOrWhiteSpace($Prompt))) -Encoding UTF8

if ($Mode -eq "fail") {
    [Console]::Error.WriteLine("FAKE_WORKER_STOPPED")
    exit 13
}

Write-Output "FAKE_WORKER_DONE"
exit 0
'@ | Set-Content -LiteralPath (Join-Path $path "scripts\Invoke-FakePipelineWorker.ps1") -Encoding UTF8

    return $path
}

function New-TaskFile {
    param(
        [Parameter(Mandatory = $true)][string]$RootPath,
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][string]$Text
    )

    $taskPath = Join-Path $RootPath ("tasks\queue\{0}" -f $Name)
    $Text | Set-Content -LiteralPath $taskPath -Encoding UTF8
    return $taskPath
}

function New-SlotObject {
    param(
        [Parameter(Mandatory = $true)][string]$RootPath,
        [ValidateSet("pass", "fail")][string]$Mode
    )

    $workerPath = Join-Path $RootPath "scripts\Invoke-FakePipelineWorker.ps1"
    return [pscustomobject]@{
        name = "headless-e2e"
        agent = "fake"
        role = "implementation"
        enabled = $true
        branch = "agent/headless-e2e"
        command = [pscustomobject]@{
            start = @("powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $workerPath, "-Mode", $Mode, "-Prompt", "{prompt}")
            resume = @("powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $workerPath, "-Mode", $Mode, "-Prompt", "{prompt}")
        }
    }
}

function New-ProjectObject {
    return [pscustomobject]@{
        name = "e2e-test-project"
        profilePath = ""
        validation = @()
    }
}

function Invoke-StartSlotE2E {
    param(
        [Parameter(Mandatory = $true)][string]$RootPath,
        [ValidateSet("pass", "fail")][string]$Mode
    )

    $slot = New-SlotObject -RootPath $RootPath -Mode $Mode
    $project = New-ProjectObject
    $worktreePath = Join-Path $RootPath "worktrees\headless-e2e"

    $previousErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $output = & powershell -NoProfile -ExecutionPolicy Bypass `
            -File $startSlotScript `
            -OrchestratorRoot $RootPath `
            -WorktreePath $worktreePath `
            -SlotJsonBase64 (ConvertTo-Base64Json -Value $slot) `
            -ProjectJsonBase64 (ConvertTo-Base64Json -Value $project) `
            -RunOnce `
            -Headless 2>&1

        $exitCode = $LASTEXITCODE
        if ($null -eq $exitCode) { $exitCode = 0 }
        return [pscustomobject]@{
            exitCode = [int]$exitCode
            output = ($output | ForEach-Object { $_.ToString() }) -join "`n"
            worktreePath = $worktreePath
        }
    }
    finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }
}

function Get-TaskCount {
    param([string]$RootPath, [string]$State)

    $dir = Join-Path $RootPath ("tasks\{0}" -f $State)
    return @(Get-ChildItem -LiteralPath $dir -File -Filter "*.md" -ErrorAction SilentlyContinue).Count
}

function Assert-FileExists {
    param([string]$Path, [string]$Message)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw $Message }
}

function Assert-FileMissing {
    param([string]$Path, [string]$Message)
    if (Test-Path -LiteralPath $Path -PathType Leaf) { throw $Message }
}

function Get-MovementAuditLines {
    param([string]$RootPath)

    $auditFiles = @(Get-ChildItem -LiteralPath (Join-Path $RootPath "reports\queue-movements") -Filter "*.jsonl" -File -ErrorAction SilentlyContinue)
    $entries = @()
    foreach ($file in $auditFiles) {
        foreach ($line in @(Get-Content -LiteralPath $file.FullName -ErrorAction Stop)) {
            if ([string]::IsNullOrWhiteSpace($line)) { continue }
            $entries += ($line | ConvertFrom-Json -ErrorAction Stop)
        }
    }
    return @($entries)
}

$passRoot = $null
$failRoot = $null
try {
    $passRoot = New-PipelineRoot
    New-TaskFile -RootPath $passRoot -Name "p0-e2e-pipeline-pass.md" -Text @'
# P0 E2E pipeline pass

Priority: P0
Issue: #196

Recover headless local-shell queue claim behavior for disaster recovery.
'@ | Out-Null

    $pass = Invoke-StartSlotE2E -RootPath $passRoot -Mode pass
    if ($pass.exitCode -ne 0) { throw "Successful E2E slot run exited $($pass.exitCode): $($pass.output)" }

    Assert-FileMissing -Path (Join-Path $passRoot "tasks\queue\p0-e2e-pipeline-pass.md") -Message "Successful pipeline should remove queued source."
    Assert-FileMissing -Path (Join-Path $passRoot "tasks\active\headless-e2e__p0-e2e-pipeline-pass.md") -Message "Successful pipeline should not leave active task."
    Assert-FileExists -Path (Join-Path $passRoot "tasks\done\p0-e2e-pipeline-pass.md") -Message "Successful pipeline should move task to done."
    if (Get-TaskCount -RootPath $passRoot -State "failed") { throw "Successful pipeline should not create failed tasks." }

    $agentLog = Join-Path $pass.worktreePath "AGENT_LOG.md"
    Assert-FileExists -Path $agentLog -Message "Successful pipeline should leave an AGENT_LOG.md in the worktree."
    if ((Get-Content -LiteralPath $agentLog -Raw) -notmatch "Fake worker mode=pass") { throw "Successful pipeline did not run the fake worker." }

    $passAudit = Get-MovementAuditLines -RootPath $passRoot
    if (@($passAudit | Where-Object { $_.from -eq "queue" -and $_.to -eq "active" -and $_.slot -eq "headless-e2e" }).Count -ne 1) {
        throw "Successful pipeline did not audit queue -> active claim."
    }
    if (@($passAudit | Where-Object { $_.from -eq "active" -and $_.to -eq "done" }).Count -ne 1) {
        throw "Successful pipeline did not audit active -> done completion."
    }

    $failRoot = New-PipelineRoot
    New-TaskFile -RootPath $failRoot -Name "p0-e2e-pipeline-fail.md" -Text @'
# P0 E2E pipeline fail

Priority: P0
Issue: #196

Recover headless local-shell queue claim behavior for disaster recovery.
'@ | Out-Null
    New-TaskFile -RootPath $failRoot -Name "p0-e2e-second-task.md" -Text @'
# P0 E2E second task

Priority: P0
Issue: #196

This second task proves the pipeline stops after the first worker failure.
'@ | Out-Null

    $fail = Invoke-StartSlotE2E -RootPath $failRoot -Mode fail

    Assert-FileMissing -Path (Join-Path $failRoot "tasks\done\p0-e2e-pipeline-fail.md") -Message "Failed pipeline must not mark the failed task done."
    Assert-FileExists -Path (Join-Path $failRoot "tasks\queue\p0-e2e-second-task.md") -Message "Failed pipeline must stop after one failed worker and leave later work queued."

    $failedTask = Join-Path $failRoot "tasks\failed\p0-e2e-pipeline-fail.md"
    $activeTask = Join-Path $failRoot "tasks\active\headless-e2e__p0-e2e-pipeline-fail.md"
    if (-not ((Test-Path -LiteralPath $failedTask -PathType Leaf) -or (Test-Path -LiteralPath $activeTask -PathType Leaf))) {
        throw "Failed pipeline must preserve the failed work in failed or active state. Output: $($fail.output)"
    }

    Assert-FileMissing -Path (Join-Path $failRoot "tasks\done\p0-e2e-second-task.md") -Message "Failed pipeline must not complete later queued work."
    Assert-FileMissing -Path (Join-Path $failRoot "tasks\active\headless-e2e__p0-e2e-second-task.md") -Message "Failed pipeline must not claim later queued work."

    $failAudit = Get-MovementAuditLines -RootPath $failRoot
    if (@($failAudit | Where-Object { $_.from -eq "queue" -and $_.to -eq "active" -and $_.slot -eq "headless-e2e" }).Count -ne 1) {
        throw "Failed pipeline should audit exactly one queue -> active claim."
    }
    if (@($failAudit | Where-Object { $_.taskName -match "p0-e2e-second-task" }).Count -ne 0) {
        throw "Failed pipeline must not move or audit the second queued task."
    }

    Write-Host "Work pipeline E2E tests passed."
}
finally {
    if ($passRoot) { Remove-Item -LiteralPath $passRoot -Recurse -Force -ErrorAction SilentlyContinue }
    if ($failRoot) { Remove-Item -LiteralPath $failRoot -Recurse -Force -ErrorAction SilentlyContinue }
}
