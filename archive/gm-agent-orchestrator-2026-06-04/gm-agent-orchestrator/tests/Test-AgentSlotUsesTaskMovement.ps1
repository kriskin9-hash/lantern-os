[CmdletBinding()]
param(
    [string]$Root = (Resolve-Path "$PSScriptRoot\..").Path
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$slotScript = Join-Path $Root 'scripts\Start-AgentSlot.ps1'
$moveScript = Join-Path $Root 'scripts\Move-OrchestratorTask.ps1'

if (-not (Test-Path $slotScript)) {
    throw "Agent slot script was not found: $slotScript"
}

if (-not (Test-Path $moveScript)) {
    throw "Task movement helper was not found: $moveScript"
}

$content = Get-Content $slotScript -Raw

if ($content -notmatch 'Move-OrchestratorTask\.ps1') {
    throw 'Start-AgentSlot.ps1 must call scripts\Move-OrchestratorTask.ps1 for queue state transitions.'
}

if ($content -match 'Move-Item\s+-Path\s+\$task\.FullName') {
    throw 'Start-AgentSlot.ps1 still claims queued tasks with raw Move-Item instead of Move-OrchestratorTask.ps1.'
}

if ($content -match 'Move-Item\s+-Path\s+\$TaskPath') {
    throw 'Start-AgentSlot.ps1 still completes/fails active tasks with raw Move-Item instead of Move-OrchestratorTask.ps1.'
}

Write-Host 'Agent slot task movement helper usage test passed.'
