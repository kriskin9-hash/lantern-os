[CmdletBinding()]
param(
    [string]$Root = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Root)) {
    $Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}
else {
    $Root = (Resolve-Path $Root).Path
}

$statusScript = Join-Path $Root "scripts\Get-OrchestratorStatus.ps1"
$outputPath = Join-Path $Root "status\active-fleet-plan.json"
$activeProcessingConfigPath = Join-Path $Root "config\active-processing.json"
$agentsConfigPath = Join-Path $Root "config\agents.json"

function Get-OptionalProperty {
    param(
        [object]$Object,
        [string]$Name
    )

    if ($null -eq $Object) { return $null }
    $property = $Object.PSObject.Properties[$Name]
    if ($null -eq $property) { return $null }
    return $property.Value
}

function Get-JsonFileOrNull {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $null }
    return (Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json -ErrorAction Stop)
}

function Get-OrchestratorStatusSnapshot {
    param([string]$RootPath)

    if (-not (Test-Path -LiteralPath $statusScript -PathType Leaf)) {
        throw "Missing required script: $statusScript"
    }

    $output = @(& powershell -NoProfile -ExecutionPolicy Bypass -File $statusScript -Root $RootPath 2>&1)
    $exitCode = $LASTEXITCODE
    $text = (($output | ForEach-Object { $_.ToString() }) -join "`n").Trim()
    if ($exitCode -ne 0) {
        throw "Get-OrchestratorStatus.ps1 failed with exit code $exitCode. Output: $text"
    }
    if ([string]::IsNullOrWhiteSpace($text)) {
        throw "Get-OrchestratorStatus.ps1 emitted no JSON."
    }

    return ($text | ConvertFrom-Json -ErrorAction Stop)
}

function ConvertTo-ChangedFile {
    param([string]$StatusLine)

    $entry = ($StatusLine | Out-String).TrimEnd()
    if ([string]::IsNullOrWhiteSpace($entry)) { return $null }

    $status = if ($entry.Length -ge 2) { $entry.Substring(0, 2).Trim() } else { $entry.Trim() }
    $path = if ($entry.Length -ge 4) { $entry.Substring(3).Trim() } else { "" }
    if ($path.StartsWith('"') -and $path.EndsWith('"') -and $path.Length -ge 2) {
        $path = $path.Substring(1, $path.Length - 2)
    }
    if ($path -like "* -> *") {
        $path = ($path -split " -> ")[-1]
    }

    return [pscustomobject]@{
        status = $status
        path = $path
    }
}

function Test-ControlPlanePath {
    param([string]$Path)

    $normalized = ($Path -replace "\\", "/").Trim()
    if ($normalized -like "scripts/*") { return $true }
    $exact = @(
        "AGENTS.md",
        "CLAUDE.md",
        ".claude/settings.local.json",
        ".claude/settings.supervised-write.json",
        "docs/agent-contract.md",
        "docs/repo-structure-contract.md",
        "docs/file-ownership-map.yml",
        "scripts/Start-GmAgentOrchestrator.ps1",
        "scripts/Start-AgentSlot.ps1",
        "scripts/Start-OrchMcpServer.ps1",
        "scripts/Start-OrchestratorServices.ps1",
        "scripts/Invoke-OrchestratorAgentAction.ps1",
        "scripts/Invoke-OrchestratorTaskAction.ps1",
        "scripts/Claim-OrchestratorQueueTask.ps1",
        "scripts/Move-OrchestratorTask.ps1"
    )

    if ($normalized -in $exact) { return $true }
    if ($normalized -like ".claude/hooks/*.ps1") { return $true }
    if ($normalized -like "scripts/Start-OrchMcpServer*.ps1") { return $true }
    return $false
}

function Get-GitSummary {
    param([string]$RootPath)

    $branchOutput = @(& git -C $RootPath rev-parse --abbrev-ref HEAD 2>$null)
    $branch = ""
    if ($LASTEXITCODE -eq 0 -and $branchOutput.Count -gt 0) {
        $branch = ($branchOutput[0] | Out-String).Trim()
    }

    $statusOutput = @(& git -C $RootPath status --porcelain=v1 2>&1)
    if ($LASTEXITCODE -ne 0) {
        return [pscustomobject]@{
            branch = $branch
            gitAvailable = $false
            dirty = $false
            changedCount = 0
            changedFiles = @()
            controlPlaneDirtyFiles = @()
            error = (($statusOutput | ForEach-Object { $_.ToString() }) -join "`n").Trim()
        }
    }

    $changedFiles = @()
    foreach ($line in $statusOutput) {
        $changed = ConvertTo-ChangedFile -StatusLine $line
        if ($null -ne $changed) {
            $changedFiles += $changed
        }
    }

    $controlPlaneDirtyFiles = @($changedFiles | Where-Object { Test-ControlPlanePath -Path $_.path })

    return [pscustomobject]@{
        branch = $branch
        gitAvailable = $true
        dirty = [bool]($changedFiles.Count -gt 0)
        changedCount = $changedFiles.Count
        changedFiles = $changedFiles
        controlPlaneDirtyFiles = $controlPlaneDirtyFiles
        error = ""
    }
}

function Get-ActiveProcessingSettings {
    param([string]$RootPath)

    $config = Get-JsonFileOrNull -Path $activeProcessingConfigPath
    $activeProcessing = Get-OptionalProperty -Object $config -Name "activeProcessing"
    $agentActivation = Get-OptionalProperty -Object $config -Name "agentActivation"
    $mcpIntegration = Get-OptionalProperty -Object $config -Name "mcpIntegration"

    $enabled = Get-OptionalProperty -Object $activeProcessing -Name "enabled"
    $immediateDispatch = Get-OptionalProperty -Object $activeProcessing -Name "immediateDispatch"
    $noQueueDelay = Get-OptionalProperty -Object $activeProcessing -Name "noQueueDelay"
    $standbyActivation = Get-OptionalProperty -Object $agentActivation -Name "standbyActivation"
    $maxActiveAgents = Get-OptionalProperty -Object $agentActivation -Name "maxActiveAgents"
    $mcpServerUrl = Get-OptionalProperty -Object $mcpIntegration -Name "serverUrl"

    return [pscustomobject]@{
        source = "config\active-processing.json"
        enabled = $(if ($null -ne $enabled) { [bool]$enabled } else { $false })
        immediateDispatch = $(if ($null -ne $immediateDispatch) { [bool]$immediateDispatch } else { $false })
        noQueueDelay = $(if ($null -ne $noQueueDelay) { [bool]$noQueueDelay } else { $false })
        standbyActivation = $(if ($null -ne $standbyActivation) { [bool]$standbyActivation } else { $false })
        maxActiveAgents = $(if ($null -ne $maxActiveAgents) { [int]$maxActiveAgents } else { 1 })
        mcpServerUrl = $(if ([string]::IsNullOrWhiteSpace([string]$mcpServerUrl)) { "http://127.0.0.1:8787" } else { [string]$mcpServerUrl })
    }
}

function Get-DispatchOrder {
    param([string]$RootPath)

    $config = Get-JsonFileOrNull -Path $agentsConfigPath
    $routingPolicy = Get-OptionalProperty -Object $config -Name "routingPolicy"
    $dispatchOrder = @(Get-OptionalProperty -Object $routingPolicy -Name "dispatchOrder")
    $orderedSlots = @()
    foreach ($entry in $dispatchOrder) {
        $slotName = [string](Get-OptionalProperty -Object $entry -Name "slot")
        if (-not [string]::IsNullOrWhiteSpace($slotName)) {
            $orderedSlots += $slotName
        }
    }
    return $orderedSlots
}

function ConvertTo-SlotSummary {
    param([object]$Slot)

    $slotName = [string](Get-OptionalProperty -Object $Slot -Name "slot")
    if ([string]::IsNullOrWhiteSpace($slotName)) {
        $slotName = [string](Get-OptionalProperty -Object $Slot -Name "name")
    }

    $safeToWake = Get-OptionalProperty -Object $Slot -Name "safeToWake"
    return [pscustomobject]@{
        slot = $slotName
        agent = [string](Get-OptionalProperty -Object $Slot -Name "agent")
        state = [string](Get-OptionalProperty -Object $Slot -Name "state")
        wakeState = [string](Get-OptionalProperty -Object $Slot -Name "wakeState")
        safeToWake = $(if ($null -ne $safeToWake) { [bool]$safeToWake } else { $false })
        reason = [string](Get-OptionalProperty -Object $Slot -Name "reason")
        nextAction = [string](Get-OptionalProperty -Object $Slot -Name "nextAction")
    }
}

function Get-OrderedCandidateSlots {
    param(
        [object[]]$Slots,
        [string[]]$DispatchOrder
    )

    $rank = @{}
    for ($i = 0; $i -lt $DispatchOrder.Count; $i++) {
        $rank[$DispatchOrder[$i]] = $i
    }

    $candidates = @($Slots | ForEach-Object { ConvertTo-SlotSummary -Slot $_ } | Where-Object {
        $_.wakeState -eq "available" -and $_.safeToWake -and $_.state -in @("idle", "recent", "available")
    })

    return @($candidates | Sort-Object `
        @{ Expression = { if ($rank.ContainsKey($_.slot)) { $rank[$_.slot] } else { [int]::MaxValue } } }, `
        @{ Expression = { $_.slot } })
}

$status = Get-OrchestratorStatusSnapshot -RootPath $Root
$activeProcessing = Get-ActiveProcessingSettings -RootPath $Root
$dispatchOrder = Get-DispatchOrder -RootPath $Root
$repo = Get-GitSummary -RootPath $Root

$serviceHealth = Get-OptionalProperty -Object $status -Name "serviceHealth"
$mcpCapability = Get-OptionalProperty -Object $serviceHealth -Name "mcpCapability"
$mcpMode = [string](Get-OptionalProperty -Object $mcpCapability -Name "mode")
$mcpWritableValue = Get-OptionalProperty -Object $mcpCapability -Name "writable"
$mcpWritable = $(if ($null -ne $mcpWritableValue) { [bool]$mcpWritableValue } else { $false })

$blockedReasons = New-Object System.Collections.Generic.List[string]
if (@($repo.controlPlaneDirtyFiles).Count -gt 0) {
    $blockedReasons.Add("local_mcp_control_plane_dirty")
    $blockedReasons.Add("inspect_required_before_retry")
}
elseif ($mcpMode -ne "online_writable" -or -not $mcpWritable) {
    $blockedReasons.Add("mcp_not_writable")
}

$availability = Get-OptionalProperty -Object $status -Name "availability"
$slots = @()
$availabilitySlots = Get-OptionalProperty -Object $availability -Name "slots"
if ($null -ne $availabilitySlots) {
    $slots = @($availabilitySlots)
}

$candidateSlots = Get-OrderedCandidateSlots -Slots $slots -DispatchOrder $dispatchOrder
$selectedSlots = @()
$futureSlotsAfterMcpFix = @()
$dispatchMode = "no_available_slots"

if ($blockedReasons.Count -gt 0) {
    $dispatchMode = "hold_for_mcp_p0"
    $futureSlotsAfterMcpFix = @($candidateSlots)
}
else {
    $selectedSlots = @($candidateSlots | Select-Object -First $activeProcessing.maxActiveAgents)
    $futureSlotsAfterMcpFix = @($selectedSlots)
    if ($selectedSlots.Count -gt 1) {
        $dispatchMode = "parallel_ready"
    }
    elseif ($selectedSlots.Count -eq 1) {
        $dispatchMode = "single_slot_ready"
    }
}

$statusNextAction = Get-OptionalProperty -Object $status -Name "nextAction"
$defaultAction = [string](Get-OptionalProperty -Object $statusNextAction -Name "action")
if ([string]::IsNullOrWhiteSpace($defaultAction)) {
    if ($blockedReasons.Count -gt 0) {
        $defaultAction = "Finish dirty local MCP/control-plane P0 work before parallel activation."
    }
    elseif ($selectedSlots.Count -gt 0) {
        $defaultAction = "Start an available slot on queued work."
    }
    else {
        $defaultAction = "No parallel-ready slots available."
    }
}

$nextAction = [pscustomobject]@{
    action = $defaultAction
    owner = $(if ([string]::IsNullOrWhiteSpace([string](Get-OptionalProperty -Object $statusNextAction -Name "owner"))) { "Alex" } else { [string](Get-OptionalProperty -Object $statusNextAction -Name "owner") })
    when = $(if ([string]::IsNullOrWhiteSpace([string](Get-OptionalProperty -Object $statusNextAction -Name "when"))) { "now" } else { [string](Get-OptionalProperty -Object $statusNextAction -Name "when") })
    blockedBy = $(if ($blockedReasons.Count -gt 0) { $blockedReasons[0] } else { [string](Get-OptionalProperty -Object $statusNextAction -Name "blockedBy") })
}

$plan = [ordered]@{
    ok = $true
    action = "active_agent_fleet_plan"
    generatedAt = (Get-Date).ToString("o")
    root = $Root
    outputPath = $outputPath
    activeProcessing = $activeProcessing
    repo = $repo
    orchestratorStatus = [pscustomobject]@{
        state = [string](Get-OptionalProperty -Object $status -Name "state")
        headline = [string](Get-OptionalProperty -Object $status -Name "headline")
        queueRecommendation = Get-OptionalProperty -Object $status -Name "queueRecommendation"
        nextAction = $statusNextAction
        availability = $availability
    }
    mcpLane = [pscustomobject]@{
        blocked = [bool]($blockedReasons.Count -gt 0)
        blockedReasons = @($blockedReasons)
        capabilityMode = $mcpMode
        writable = $mcpWritable
        nextAction = $defaultAction
    }
    parallelPlan = [pscustomobject]@{
        dispatchMode = $dispatchMode
        candidateSlots = @($candidateSlots)
        selectedSlots = @($selectedSlots)
        futureSlotsAfterMcpFix = @($futureSlotsAfterMcpFix)
        maxActiveAgents = [int]$activeProcessing.maxActiveAgents
    }
    nextAction = $nextAction
}

$outputDir = Split-Path -Parent $outputPath
if (-not [string]::IsNullOrWhiteSpace($outputDir)) {
    New-Item -ItemType Directory -Force -Path $outputDir | Out-Null
}

$json = $plan | ConvertTo-Json -Depth 20
$json | Set-Content -LiteralPath $outputPath -Encoding UTF8
Write-Output $json
