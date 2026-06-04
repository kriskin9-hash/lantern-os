[CmdletBinding()]
param(
    [string]$Root = (Resolve-Path "$PSScriptRoot\..").Path,
    [switch]$SkipMvpCi
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$statusScript = Join-Path $Root "scripts/Get-OrchestratorStatus.ps1"
if (!(Test-Path $statusScript)) {
    throw "Orchestrator status script was not found: $statusScript"
}

$requiredFields = @("generatedAt", "state", "headline", "counts", "availability", "bridgeValidation")
$output = & powershell -NoProfile -ExecutionPolicy Bypass -File $statusScript -Root $Root
$exitCode = $LASTEXITCODE

if ($exitCode -ne 0) {
    throw "Get-OrchestratorStatus.ps1 exited with code $exitCode."
}

$jsonText = ($output | Out-String).Trim()
if ([string]::IsNullOrWhiteSpace($jsonText)) {
    throw "Get-OrchestratorStatus.ps1 wrote no stdout. Expected JSON."
}

if (!$jsonText.StartsWith("{")) {
    $prefix = $jsonText.Substring(0, [Math]::Min(120, $jsonText.Length))
    throw "Get-OrchestratorStatus.ps1 stdout must start with JSON object text. Actual prefix: $prefix"
}

try {
    $status = $jsonText | ConvertFrom-Json -ErrorAction Stop
}
catch {
    throw "Get-OrchestratorStatus.ps1 stdout is not valid JSON: $($_.Exception.Message)"
}

foreach ($field in $requiredFields) {
    if ($null -eq $status.PSObject.Properties[$field]) {
        throw "Get-OrchestratorStatus.ps1 JSON is missing required top-level field: $field"
    }
}

if ($null -eq $status.counts.PSObject.Properties["queue"] -or
    $null -eq $status.counts.PSObject.Properties["active"] -or
    $null -eq $status.counts.PSObject.Properties["done"] -or
    $null -eq $status.counts.PSObject.Properties["failed"]) {
    throw "Get-OrchestratorStatus.ps1 JSON counts object is missing one or more required queue/active/done/failed fields."
}

foreach ($field in @("availableCount", "nextWakeAt", "nextWakeSlot", "nextWakeState", "nextHumanAction", "slots")) {
    if ($null -eq $status.availability.PSObject.Properties[$field]) {
        throw "Get-OrchestratorStatus.ps1 availability object is missing required field: $field"
    }
}

$availabilitySlots = @($status.availability.slots)
if ($availabilitySlots.Count -eq 0) {
    throw "Get-OrchestratorStatus.ps1 availability.slots must include at least one slot."
}

foreach ($slot in $availabilitySlots) {
    foreach ($field in @("slot", "state", "wakeState", "wakeAt", "safeToWake", "reason", "nextAction")) {
        if ($null -eq $slot.PSObject.Properties[$field]) {
            throw "Availability slot JSON is missing required field: $field"
        }
    }
}

foreach ($field in @("state", "taskPath", "logPath", "blocker", "nextAction", "chatgptFallbackPrompt")) {
    if ($null -eq $status.bridgeValidation.PSObject.Properties[$field]) {
        throw "Get-OrchestratorStatus.ps1 bridgeValidation object is missing required field: $field"
    }
}

$bridgeState = [string]$status.bridgeValidation.state
if (@("A", "B", "C", "unresolved") -notcontains $bridgeState) {
    throw "bridgeValidation.state must be one of A/B/C/unresolved. Actual: $bridgeState"
}

$taskCollections = @(
    @{ name = "tasks.queue"; value = $status.tasks.queue },
    @{ name = "tasks.active"; value = $status.tasks.active },
    @{ name = "tasks.done"; value = $status.tasks.done },
    @{ name = "tasks.failed"; value = $status.tasks.failed },
    @{ name = "slots"; value = $status.slots },
    @{ name = "activityLog"; value = $status.activityLog },
    @{ name = "priorityWarnings"; value = $status.priorityWarnings }
)
foreach ($entry in $taskCollections) {
    if ($null -eq $entry.value) {
        throw "Get-OrchestratorStatus.ps1 JSON collection field is null: $($entry.name)"
    }
    if ($entry.value -is [System.Collections.IDictionary]) {
        throw "Get-OrchestratorStatus.ps1 JSON collection field must be an array, got object: $($entry.name)"
    }
}

foreach ($slot in @($status.slots)) {
    if ($null -eq $slot) { continue }
    if ($slot.PSObject.Properties["changedFiles"] -and $slot.changedFiles -is [System.Collections.IDictionary]) {
        throw "Slot changedFiles must be an array, got object for slot: $($slot.name)"
    }
    if ($slot.PSObject.Properties["worktree"] -and $slot.worktree -and
        $slot.worktree.PSObject.Properties["changedFiles"] -and
        $slot.worktree.changedFiles -is [System.Collections.IDictionary]) {
        throw "Slot worktree.changedFiles must be an array, got object for slot: $($slot.name)"
    }
    if ($slot.PSObject.Properties["runnerEvidence"] -and $slot.runnerEvidence -and
        $slot.runnerEvidence.PSObject.Properties["processIds"] -and
        $slot.runnerEvidence.processIds -is [System.Collections.IDictionary]) {
        throw "Slot runnerEvidence.processIds must be an array, got object for slot: $($slot.name)"
    }
}

if (-not $SkipMvpCi) {
    $mvpCiScript = Join-Path $Root "tests\Test-OrchestratorMvpCi.ps1"
    if (-not (Test-Path -LiteralPath $mvpCiScript -PathType Leaf)) {
        throw "MVP CI contract test was not found: $mvpCiScript"
    }
    & powershell -NoProfile -ExecutionPolicy Bypass -File $mvpCiScript -Root $Root
    if ($LASTEXITCODE -ne 0) {
        throw "MVP CI contract test failed: $mvpCiScript"
    }
}

Write-Host "Validated orchestrator status JSON stdout, counts, and availability fields."
