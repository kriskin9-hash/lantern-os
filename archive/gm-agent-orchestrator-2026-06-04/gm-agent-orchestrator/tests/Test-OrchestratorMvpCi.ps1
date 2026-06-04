[CmdletBinding()]
param(
    [string]$Root = (Resolve-Path "$PSScriptRoot\..").Path
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root = (Resolve-Path $Root).Path
$statusScript = Join-Path $Root "scripts\Get-OrchestratorStatus.ps1"
$queueCreateScript = Join-Path $Root "scripts\New-OrchestratorQueueTask.ps1"
$taskActionScript = Join-Path $Root "scripts\Invoke-OrchestratorTaskAction.ps1"
$agentActionScript = Join-Path $Root "scripts\Invoke-OrchestratorAgentAction.ps1"
$dashboardPath = Join-Path $Root "dashboard\index.html"

foreach ($script in @($statusScript, $queueCreateScript, $taskActionScript, $agentActionScript)) {
    if (-not (Test-Path -LiteralPath $script -PathType Leaf)) {
        throw "MVP CI required helper script is missing: $script"
    }
}

if (-not (Test-Path -LiteralPath $dashboardPath -PathType Leaf)) {
    throw "MVP CI dashboard entry point is missing: $dashboardPath"
}

function Assert-Property {
    param(
        [Parameter(Mandatory)]$Object,
        [Parameter(Mandatory)][string]$Name,
        [Parameter(Mandatory)][string]$Context
    )

    if ($null -eq $Object -or $null -eq $Object.PSObject.Properties[$Name]) {
        throw "$Context is missing required property: $Name"
    }
}

function Convert-JsonOutput {
    param(
        [Parameter(Mandatory)][object[]]$Output,
        [Parameter(Mandatory)][string]$Context
    )

    $jsonText = ($Output | Out-String).Trim()
    if ([string]::IsNullOrWhiteSpace($jsonText)) {
        throw "$Context wrote no stdout. Expected JSON."
    }
    if (-not $jsonText.StartsWith("{")) {
        $prefix = $jsonText.Substring(0, [Math]::Min(120, $jsonText.Length))
        throw "$Context stdout must start with a JSON object. Actual prefix: $prefix"
    }
    return $jsonText | ConvertFrom-Json -ErrorAction Stop
}

$statusOutput = & powershell -NoProfile -ExecutionPolicy Bypass -File $statusScript -Root $Root 2>&1
if ($LASTEXITCODE -ne 0) {
    throw "Get-OrchestratorStatus.ps1 failed in MVP CI contract: $($statusOutput -join "`n")"
}
$status = Convert-JsonOutput -Output $statusOutput -Context "Get-OrchestratorStatus.ps1"

foreach ($field in @("generatedAt", "state", "headline", "counts", "availability", "tasks")) {
    Assert-Property -Object $status -Name $field -Context "MVP status JSON"
}

foreach ($field in @("queue", "active", "done", "failed")) {
    Assert-Property -Object $status.counts -Name $field -Context "MVP status counts"
    Assert-Property -Object $status.tasks -Name $field -Context "MVP status tasks"
}

foreach ($field in @("availableCount", "nextWakeAt", "nextWakeSlot", "nextWakeState", "nextHumanAction", "slots")) {
    Assert-Property -Object $status.availability -Name $field -Context "MVP availability"
}

$availabilitySlots = @($status.availability.slots)
if ($availabilitySlots.Count -eq 0) {
    throw "MVP availability must include at least one slot."
}

foreach ($slot in $availabilitySlots) {
    foreach ($field in @("slot", "agent", "state", "wakeState", "safeToWake", "reason", "nextAction")) {
        Assert-Property -Object $slot -Name $field -Context "MVP availability slot"
    }
}

$slotDetails = @()
if ($null -ne $status.PSObject.Properties["agents"]) {
    $slotDetails = @($status.agents)
}
elseif ($null -ne $status.PSObject.Properties["slots"]) {
    $slotDetails = @($status.slots)
}

foreach ($slot in $slotDetails) {
    foreach ($field in @("name", "state", "nextAction")) {
        Assert-Property -Object $slot -Name $field -Context "MVP slot detail"
    }
    if ($null -ne $slot.PSObject.Properties["worktree"]) {
        Assert-Property -Object $slot.worktree -Name "changedFiles" -Context "MVP slot worktree"
    }
}

$statusArtifact = Join-Path $Root "status\orchestrator.json"
if (-not (Test-Path -LiteralPath $statusArtifact -PathType Leaf)) {
    throw "MVP status run must write status/orchestrator.json for dashboard consumption."
}
Get-Content -LiteralPath $statusArtifact -Raw | ConvertFrom-Json -ErrorAction Stop | Out-Null

$dashboardText = Get-Content -LiteralPath $dashboardPath -Raw
foreach ($needle in @("orchestrator", "queue", "active", "status")) {
    if ($dashboardText -notmatch [regex]::Escape($needle)) {
        throw "Dashboard MVP entry point should reference $needle."
    }
}

$tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("orch-mvp-ci-{0}" -f [Guid]::NewGuid().ToString("N"))
try {
    foreach ($relativePath in @(
        "tasks\queue",
        "tasks\active",
        "tasks\done",
        "tasks\failed",
        "logs",
        "locks",
        "status",
        "reports\dashboard",
        "config"
    )) {
        New-Item -ItemType Directory -Force -Path (Join-Path $tempRoot $relativePath) | Out-Null
    }

    @'
{
  "fallbackWaitMinutes": 300,
  "maxResumeCycles": 4,
  "slots": [
    {
      "name": "operator-intake",
      "agent": "human-interface",
      "role": "operator-intake",
      "enabled": true,
      "branch": "agent/operator-intake",
      "command": {
        "start": ["powershell", "-NoProfile", "-Command", "Write-Output intake"],
        "resume": ["powershell", "-NoProfile", "-Command", "Write-Output intake"]
      }
    }
  ]
}
'@ | Set-Content -LiteralPath (Join-Path $tempRoot "config\agents.json") -Encoding UTF8

    @'
{
  "worktreeRoot": "worktrees"
}
'@ | Set-Content -LiteralPath (Join-Path $tempRoot "config\projects.json") -Encoding UTF8

    $body = @'
## Problem
MVP CI must prove a human can stock the queue with one helper call.

## Acceptance criteria
- Queue creation validates input.
- Dry-run does not mutate queue counts.
- Audit metadata is returned.
'@

    $dryRunOutput = & powershell -NoProfile -ExecutionPolicy Bypass -File $queueCreateScript `
        -Root $tempRoot `
        -Title "P0: MVP CI dry-run queue task" `
        -Body $body `
        -Priority P0 `
        -Owner operator-intake `
        -DryRun 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "MVP queue creation dry-run failed: $($dryRunOutput -join "`n")"
    }
    $dryRun = Convert-JsonOutput -Output $dryRunOutput -Context "New-OrchestratorQueueTask.ps1 -DryRun"
    if (-not $dryRun.ok -or -not $dryRun.dryRun) {
        throw "MVP queue creation dry-run must return ok=true and dryRun=true."
    }
    if ($dryRun.afterCounts.queue -ne $dryRun.beforeCounts.queue) {
        throw "MVP queue creation dry-run must not mutate queue counts."
    }
    if ($dryRun.audit.path -notmatch "logs/control-actions/.+create_queue_task\.json") {
        throw "MVP queue creation dry-run must return audit metadata."
    }
}
finally {
    Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host "Validated orchestrator MVP CI contract."
