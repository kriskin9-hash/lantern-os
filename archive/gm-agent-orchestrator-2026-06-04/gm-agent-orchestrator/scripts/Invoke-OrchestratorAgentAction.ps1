[CmdletBinding()]
param(
    [string]$Root = "",
    [Parameter(Mandatory = $true)]
    [ValidateSet("start_agent", "rerun_agent")]
    [string]$Action,
    [Parameter(Mandatory = $true)]
    [ValidatePattern("^[A-Za-z0-9._-]+$")]
    [string]$SlotName,
    [string]$TaskPath = "",
    [string]$TaskName = "",
    [switch]$DryRun,
    [switch]$Supervised
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Root)) {
    $Root = (Resolve-Path "$PSScriptRoot\..").Path
}
else {
    $Root = (Resolve-Path $Root).Path
}

function Get-CountMap {
    return [pscustomobject]@{
        queue = @($(if (Test-Path (Join-Path $Root "tasks\queue")) { Get-ChildItem (Join-Path $Root "tasks\queue") -File -Filter "*.md" -ErrorAction SilentlyContinue })).Count
        active = @($(if (Test-Path (Join-Path $Root "tasks\active")) { Get-ChildItem (Join-Path $Root "tasks\active") -File -Filter "*.md" -ErrorAction SilentlyContinue })).Count
        done = @($(if (Test-Path (Join-Path $Root "tasks\done")) { Get-ChildItem (Join-Path $Root "tasks\done") -File -Filter "*.md" -ErrorAction SilentlyContinue })).Count
        failed = @($(if (Test-Path (Join-Path $Root "tasks\failed")) { Get-ChildItem (Join-Path $Root "tasks\failed") -File -Filter "*.md" -ErrorAction SilentlyContinue })).Count
    }
}

function Write-AuditEvent {
    param([object]$Payload)
    $dir = Join-Path $Root "logs\control-actions"
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    $path = Join-Path $dir ("{0}-{1}-{2}.json" -f (Get-Date -Format "yyyyMMdd-HHmmss"), $Action, $SlotName)
    $Payload | ConvertTo-Json -Depth 20 | Set-Content -Path $path -Encoding UTF8
    return $path
}

function Get-ConfiguredSlot {
    $agentsPath = Join-Path $Root "config\agents.json"
    if (!(Test-Path $agentsPath)) { throw "Missing agents config: $agentsPath" }
    $agents = Get-Content $agentsPath -Raw | ConvertFrom-Json
    $slot = @($agents.slots | Where-Object { $_.name -eq $SlotName } | Select-Object -First 1)
    if ($slot.Count -eq 0) { return $null }
    return $slot[0]
}

function Get-SlotWorktreeState {
    param([string]$SlotName)
    $projectsPath = Join-Path $Root "config\projects.json"
    if (!(Test-Path $projectsPath)) { return $null }
    $projects = Get-Content $projectsPath -Raw | ConvertFrom-Json
    $worktreeRoot = [string]$projects.worktreeRoot
    if ([string]::IsNullOrWhiteSpace($worktreeRoot)) { return $null }
    $worktreePath = Join-Path $worktreeRoot $SlotName
    if (!(Test-Path $worktreePath)) { return $null }
    $lines = @(git -C $worktreePath status --porcelain 2>$null)
    return [pscustomobject]@{ path = $worktreePath; changedCount = $lines.Count; changedFiles = $lines }
}

function Get-ActiveTaskForSlot {
    param([string]$SlotName)

    $activeDir = Join-Path $Root "tasks\active"
    if (!(Test-Path -LiteralPath $activeDir -PathType Container)) { return $null }
    return @(
        Get-ChildItem -LiteralPath $activeDir -File -Filter "$SlotName`__*.md" -ErrorAction SilentlyContinue |
            Sort-Object LastWriteTime -Descending |
            Select-Object -First 1
    ) | Select-Object -First 1
}

function Get-GeminiPreflightBlocker {
    param([string]$SlotName)

    if ($SlotName -notmatch "^(?i)gemini") { return "" }

    $preflightPath = Join-Path $Root "status\gemini-preflight.json"
    if (!(Test-Path -LiteralPath $preflightPath -PathType Leaf)) {
        return "Gemini slot '$SlotName' requires a successful MCP-aware preflight before dispatch. Run scripts\Test-GeminiCliPreflight.ps1 first."
    }

    try {
        $preflight = Get-Content -LiteralPath $preflightPath -Raw | ConvertFrom-Json -ErrorAction Stop
    }
    catch {
        return "Gemini preflight status is unreadable: $($_.Exception.Message). Rerun scripts\Test-GeminiCliPreflight.ps1 before dispatch."
    }

    $recommendedNext = [string]$preflight.recommendedNext
    $mcpIssueDetected = $false
    if ($preflight.PSObject.Properties["mcpIssueDetected"]) { $mcpIssueDetected = [bool]$preflight.mcpIssueDetected }
    if ($recommendedNext -ne "evaluate" -or $mcpIssueDetected) {
        $evidence = if ($preflight.PSObject.Properties["mcpIssueEvidence"]) { [string]$preflight.mcpIssueEvidence } else { "" }
        if ([string]::IsNullOrWhiteSpace($evidence) -and $preflight.PSObject.Properties["errors"]) {
            $evidence = (@($preflight.errors) | Select-Object -First 2) -join "; "
        }
        return "Gemini preflight blocks '$SlotName' (recommendedNext=$recommendedNext, mcpIssueDetected=$mcpIssueDetected). $evidence"
    }

    return ""
}

function Write-BlockedResult {
    param([string]$Message)

    $result.ok = $false
    $result.blocked = $true
    $result.error = $Message
    $result.warnings = @($Message)
    $result.afterCounts = Get-CountMap
    [pscustomobject]$result | ConvertTo-Json -Depth 20
}

$result = [ordered]@{
    ok = $true
    action = $Action
    slot = $SlotName
    taskPath = $TaskPath
    taskName = $TaskName
    generatedAt = (Get-Date).ToString("o")
    root = $Root
    dryRun = [bool]$DryRun
    supervised = [bool]$Supervised
    claim = $null
    projectBinding = ""
    command = @()
    processId = $null
    stdoutPath = ""
    stderrPath = ""
    beforeCounts = Get-CountMap
    afterCounts = $null
    auditPath = ""
    error = ""
}

# Bind start/rerun launches to the orchestrator repo by default so queue claim and
# installed TASK_QUEUE.md are resolved within the same project/worktree domain.
$projectRepoPath = $Root
$result.projectBinding = $projectRepoPath

try {
    if (-not [string]::IsNullOrWhiteSpace($TaskPath) -and -not [string]::IsNullOrWhiteSpace($TaskName)) {
        throw "Specify only one exact task selector: TaskPath or TaskName."
    }

    $configuredSlot = Get-ConfiguredSlot
    if ($null -eq $configuredSlot) {
        throw "Unknown slot '$SlotName'. Slot must exist in config\\agents.json before dispatch."
    }
    if (-not [bool]$configuredSlot.enabled) {
        throw "Slot '$SlotName' is disabled in config\\agents.json."
    }

    if ($Action -eq "start_agent") {
        $activeTask = Get-ActiveTaskForSlot -SlotName $SlotName
        if ($null -ne $activeTask) {
            $msg = "Slot '$SlotName' already has an active task: $($activeTask.Name). Resolve, requeue, or fail the active task before dispatching new work."
            if ($DryRun) { Write-BlockedResult -Message $msg; return }
            throw $msg
        }

    }

    $worktreeState = Get-SlotWorktreeState -SlotName $SlotName
    if ($null -ne $worktreeState -and $worktreeState.changedCount -gt 0) {
        $fileList = ($worktreeState.changedFiles | Select-Object -First 10) -join ", "
        $msg = "Worktree '$SlotName' has uncommitted changes. Clean the worktree before dispatching. Changed: $fileList"
        if ($DryRun) {
            # Emit structured JSON refusal — never Write-Warning here because stderr is
            # captured via 2>&1 in Invoke-JsonScript and would appear before the JSON
            # payload, causing ConvertFrom-Json to fail with "Invalid JSON primitive: WARNING".
            $result.ok = $false
            $result.blocked = $true
            $result.error = $msg
            $result.warnings = @($msg)
            $result.afterCounts = Get-CountMap
            [pscustomobject]$result | ConvertTo-Json -Depth 20
            return
        } else {
            throw $msg
        }
    }

    if ($Action -eq "start_agent") {
        $geminiBlocker = Get-GeminiPreflightBlocker -SlotName $SlotName
        if (-not [string]::IsNullOrWhiteSpace($geminiBlocker)) {
            if ($DryRun) { Write-BlockedResult -Message $geminiBlocker; return }
            throw $geminiBlocker
        }
    }

    $claimScript = Join-Path $Root "scripts\Claim-OrchestratorQueueTask.ps1"
    if (!(Test-Path $claimScript)) { throw "Missing claim helper: $claimScript" }

    $claimSplat = [hashtable]@{ Root = $Root; SlotName = $SlotName; PassThru = $true }
    if ($DryRun) { $claimSplat["DryRun"] = $true }
    if (-not [string]::IsNullOrWhiteSpace($TaskPath)) { $claimSplat["TaskPath"] = $TaskPath }
    if (-not [string]::IsNullOrWhiteSpace($TaskName)) { $claimSplat["TaskName"] = $TaskName }
    $claim = & $claimScript @claimSplat
    $result.claim = $claim

    if (-not $claim.ok) {
        throw "Claim failed: $($claim.error)"
    }

    if ($claim.state -ne "claimed" -and $claim.state -ne "claim_dry_run") {
        $result.ok = $false
        $result.error = [string]$claim.state
        $result.afterCounts = Get-CountMap
        $result.auditPath = Write-AuditEvent -Payload ([pscustomobject]$result)
        [pscustomobject]$result | ConvertTo-Json -Depth 20
        return
    }

    $scriptPath = Join-Path $Root "scripts\Start-GmAgentOrchestrator.ps1"
    if (!(Test-Path $scriptPath)) { throw "Missing Start-GmAgentOrchestrator.ps1: $scriptPath" }

    $startArgs = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $scriptPath, "-SlotName", $SlotName, "-ProjectRepoPath", $projectRepoPath, "-RunOnce")
    if ($claim.state -eq "claimed" -and $claim.PSObject.Properties["activePath"] -and -not [string]::IsNullOrWhiteSpace([string]$claim.activePath)) {
        $startArgs += @("-ClaimedTaskRelativePath", [string]$claim.activePath)
    }
    if ($Supervised) { $startArgs += "-Supervised" }
    $result.command = @("powershell") + $startArgs

    if (-not $DryRun) {
        if ($Supervised) {
            $output = & powershell @startArgs
            if ($LASTEXITCODE -ne 0) {
                throw "Start-GmAgentOrchestrator.ps1 exited with code $LASTEXITCODE"
            }

            if ($output) {
                $jsonText = (($output | ForEach-Object { $_.ToString() }) -join "`n")
                try {
                    $launchResult = $jsonText | ConvertFrom-Json -ErrorAction Stop
                    if ($launchResult.PSObject.Properties["results"] -and @($launchResult.results).Count -gt 0) {
                        $slotLaunch = @($launchResult.results | Where-Object { $_.slot -eq $SlotName } | Select-Object -First 1)
                        if ($slotLaunch.Count -gt 0) {
                            $launch = $slotLaunch[0]
                            $result.processId = $launch.processId
                            $result.stdoutPath = [string]$launch.stdoutPath
                            $result.stderrPath = [string]$launch.stderrPath
                        }
                    }
                }
                catch {}
            }
        }
        else {
            $process = Start-Process -FilePath "powershell" -ArgumentList $startArgs -WorkingDirectory $Root -WindowStyle Hidden -PassThru
            $result.processId = $process.Id
        }
    }

    $result.afterCounts = Get-CountMap
    $result.auditPath = Write-AuditEvent -Payload ([pscustomobject]$result)
}
catch {
    $result.ok = $false
    $result.error = $_.Exception.Message
    $result.afterCounts = Get-CountMap
}

[pscustomobject]$result | ConvertTo-Json -Depth 20
