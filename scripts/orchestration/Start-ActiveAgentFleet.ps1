[CmdletBinding()]
param(
    [string]$Root = "",
    [string]$OutputPath = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Root)) {
    $Root = (Resolve-Path "$PSScriptRoot\..").Path
}
else {
    $Root = (Resolve-Path $Root).Path
}

if ([string]::IsNullOrWhiteSpace($OutputPath)) {
    $OutputPath = Join-Path $Root "status\active-fleet-plan.json"
}
elseif (-not [System.IO.Path]::IsPathRooted($OutputPath)) {
    $OutputPath = Join-Path $Root $OutputPath
}

function Get-RelativePath {
    param([string]$Path)
    if ([string]::IsNullOrWhiteSpace($Path)) { return "" }
    return $Path.Replace($Root, "").TrimStart("\")
}

function Read-JsonFileOrNull {
    param([string]$Path)
    if ([string]::IsNullOrWhiteSpace($Path) -or -not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $null }
    try { return Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json -ErrorAction Stop }
    catch { return $null }
}

function Get-ConfigPath {
    param([string]$Name)
    $local = Join-Path $Root ("config\{0}.json" -f $Name)
    $example = Join-Path $Root ("config\{0}.example.json" -f $Name)
    if (Test-Path -LiteralPath $local -PathType Leaf) { return $local }
    if (Test-Path -LiteralPath $example -PathType Leaf) { return $example }
    return ""
}

function Get-OptionalJsonProperty {
    param(
        [object]$Object,
        [string]$Name
    )
    if ($null -eq $Object) { return $null }
    if ($null -eq $Object.PSObject.Properties[$Name]) { return $null }
    return $Object.PSObject.Properties[$Name].Value
}

function Invoke-OrchestratorStatusSnapshot {
    $statusScript = Join-Path $Root "scripts\Get-OrchestratorStatus.ps1"
    if (-not (Test-Path -LiteralPath $statusScript -PathType Leaf)) {
        throw "Required status script was not found: $statusScript"
    }

    $output = @(& powershell -NoProfile -ExecutionPolicy Bypass -File $statusScript -Root $Root 2>&1)
    if ($LASTEXITCODE -ne 0) {
        throw "Get-OrchestratorStatus.ps1 failed with exit code $LASTEXITCODE. Output: $($output -join "`n")"
    }

    $text = ($output | ForEach-Object { $_.ToString() }) -join "`n"
    if ([string]::IsNullOrWhiteSpace($text)) {
        throw "Get-OrchestratorStatus.ps1 returned no JSON output."
    }

    return $text | ConvertFrom-Json -ErrorAction Stop
}

function Normalize-RepoPath {
    param([string]$Path)
    if ([string]::IsNullOrWhiteSpace($Path)) { return "" }
    return (($Path -replace "\\", "/").TrimStart("./"))
}

function Test-IsMcpControlPlanePath {
    param([string]$Path)
    $normalized = Normalize-RepoPath -Path $Path
    return $normalized -match '^(config/active-processing\.json|scripts/(Get-OrchMcpCapabilityStatus|Get-OrchestratorStatus|Get-TaskStatusViaMcp|Invoke-OrchestratorAgentAction|Monitor-ServerHealthPulse|Start-ActiveAgentFleet|Start-AgentSlot|Start-Dashboard|Start-GptWebAgent|Start-OrchMcpServer(\.Tools)?|Start-OrchestratorServices)\.ps1|tests/Test-(DashboardServiceHealthContract|OrchMcp.*|ServerHealthPulse|OrchestratorAgentActionStatusGate|OrchestratorStatus.*)\.ps1)$'
}

function Get-RepoState {
    $result = [ordered]@{
        branch = ""
        dirty = $false
        changedCount = 0
        changedFiles = @()
        controlPlaneDirtyFiles = @()
        gitAvailable = $false
        error = ""
    }

    try {
        $null = & git -C $Root rev-parse --show-toplevel 2>$null
        if ($LASTEXITCODE -ne 0) { return [pscustomobject]$result }
        $result.gitAvailable = $true

        $lines = @(& git -C $Root status --short --branch --untracked-files=all 2>&1)
        if ($LASTEXITCODE -ne 0) {
            $result.error = ($lines -join "`n")
            return [pscustomobject]$result
        }

        if ($lines.Count -gt 0) {
            $first = [string]$lines[0]
            if ($first -like '## *') {
                $branchText = $first.Substring(3).Trim()
                $result.branch = ($branchText -split '\.\.\.')[0].Trim()
            }
        }

        $changed = @()
        foreach ($line in @($lines | Select-Object -Skip 1)) {
            $text = [string]$line
            if ([string]::IsNullOrWhiteSpace($text) -or $text.Length -lt 4) { continue }
            $pathText = $text.Substring(3).Trim()
            $normalized = Normalize-RepoPath -Path $pathText
            $changed += [pscustomobject]@{
                status = $text.Substring(0, 2).Trim()
                path = $pathText
                normalizedPath = $normalized
                mcpControlPlane = (Test-IsMcpControlPlanePath -Path $normalized)
            }
        }

        $result.changedFiles = @($changed)
        $result.changedCount = @($changed).Count
        $result.dirty = $result.changedCount -gt 0
        $result.controlPlaneDirtyFiles = @($changed | Where-Object { $_.mcpControlPlane })
        return [pscustomobject]$result
    }
    catch {
        $result.error = $_.Exception.Message
        return [pscustomobject]$result
    }
}

function Get-DispatchOrderMap {
    $map = @{}
    $configPath = Get-ConfigPath -Name "agents"
    $config = Read-JsonFileOrNull -Path $configPath
    $routingPolicy = Get-OptionalJsonProperty -Object $config -Name "routingPolicy"
    $dispatchOrder = @()
    if ($null -ne $routingPolicy) {
        $dispatchOrder = @(Get-OptionalJsonProperty -Object $routingPolicy -Name "dispatchOrder")
    }

    $index = 0
    foreach ($entry in @($dispatchOrder)) {
        $slot = [string](Get-OptionalJsonProperty -Object $entry -Name "slot")
        if ([string]::IsNullOrWhiteSpace($slot)) { continue }
        $map[$slot] = $index
        $index++
    }

    return $map
}

function ConvertTo-Bool {
    param([object]$Value)
    if ($null -eq $Value) { return $false }
    return [bool]$Value
}

function ConvertTo-ArrayValue {
    param([object]$Value)
    if ($null -eq $Value) { return ,@() }
    if ($Value -is [System.Collections.IDictionary]) { return ,@() }
    return ,@($Value)
}

function Get-EligibleParallelSlots {
    param(
        [object]$Status,
        [hashtable]$DispatchOrderMap,
        [int]$MaxActiveAgents
    )

    $slots = @()
    $availability = Get-OptionalJsonProperty -Object $Status -Name "availability"
    if ($null -ne $availability) {
        $slots = @(Get-OptionalJsonProperty -Object $availability -Name "slots")
    }

    $eligible = @(
        $slots |
            Where-Object {
                (ConvertTo-Bool (Get-OptionalJsonProperty -Object $_ -Name "safeToWake")) -and
                [string](Get-OptionalJsonProperty -Object $_ -Name "wakeState") -eq "available" -and
                [string](Get-OptionalJsonProperty -Object $_ -Name "slot") -ne "operator-intake"
            } |
            Sort-Object @{
                Expression = {
                    $slotName = [string](Get-OptionalJsonProperty -Object $_ -Name "slot")
                    if ($DispatchOrderMap.ContainsKey($slotName)) { return [int]$DispatchOrderMap[$slotName] }
                    return 9999
                }
            }, @{
                Expression = { [string](Get-OptionalJsonProperty -Object $_ -Name "slot") }
            } |
            ForEach-Object {
                [pscustomobject]@{
                    slot = [string](Get-OptionalJsonProperty -Object $_ -Name "slot")
                    agent = [string](Get-OptionalJsonProperty -Object $_ -Name "agent")
                    state = [string](Get-OptionalJsonProperty -Object $_ -Name "state")
                    wakeState = [string](Get-OptionalJsonProperty -Object $_ -Name "wakeState")
                    safeToWake = ConvertTo-Bool (Get-OptionalJsonProperty -Object $_ -Name "safeToWake")
                    reason = [string](Get-OptionalJsonProperty -Object $_ -Name "reason")
                    nextAction = [string](Get-OptionalJsonProperty -Object $_ -Name "nextAction")
                }
            }
    )

    $selected = @($eligible | Select-Object -First ([Math]::Max(0, $MaxActiveAgents)))
    return [pscustomobject]@{
        candidates = @($eligible)
        selected = @($selected)
    }
}

function Get-BlockedReasons {
    param(
        [object]$RepoState,
        [object]$Status,
        [bool]$ActiveProcessingEnabled
    )

    $reasons = New-Object System.Collections.Generic.List[string]
    if (-not $ActiveProcessingEnabled) {
        $reasons.Add("active_processing_disabled") | Out-Null
    }
    if ($RepoState.controlPlaneDirtyFiles.Count -gt 0) {
        $reasons.Add("local_mcp_control_plane_dirty") | Out-Null
    }

    $queueRecommendation = Get-OptionalJsonProperty -Object $Status -Name "queueRecommendation"
    if ($null -ne $queueRecommendation) {
        $action = [string](Get-OptionalJsonProperty -Object $queueRecommendation -Name "recommendedAction")
        $from = [string](Get-OptionalJsonProperty -Object $queueRecommendation -Name "from")
        if ($action -eq "inspect" -and $from -in @("active", "failed")) {
            $reasons.Add("inspect_required_before_retry") | Out-Null
        }
    }

    $serviceHealth = Get-OptionalJsonProperty -Object $Status -Name "serviceHealth"
    $mcpCapability = $null
    if ($null -ne $serviceHealth) {
        $mcpCapability = Get-OptionalJsonProperty -Object $serviceHealth -Name "mcpCapability"
    }
    if ($null -ne $mcpCapability) {
        $writable = ConvertTo-Bool (Get-OptionalJsonProperty -Object $mcpCapability -Name "writable")
        $mode = [string](Get-OptionalJsonProperty -Object $mcpCapability -Name "mode")
        if (-not $writable -or $mode -ne "online_writable") {
            $reasons.Add("mcp_not_online_writable") | Out-Null
        }
    }

    return @($reasons)
}

function Get-ActiveProcessingConfig {
    $configPath = Get-ConfigPath -Name "active-processing"
    $config = Read-JsonFileOrNull -Path $configPath
    $activeProcessing = Get-OptionalJsonProperty -Object $config -Name "activeProcessing"
    $agentActivation = Get-OptionalJsonProperty -Object $config -Name "agentActivation"
    $mcpIntegration = Get-OptionalJsonProperty -Object $config -Name "mcpIntegration"

    $enabled = $true
    if ($null -ne $activeProcessing) {
        $enabled = ConvertTo-Bool (Get-OptionalJsonProperty -Object $activeProcessing -Name "enabled")
    }

    $maxActiveAgents = 1
    if ($null -ne $agentActivation) {
        $value = Get-OptionalJsonProperty -Object $agentActivation -Name "maxActiveAgents"
        if ($null -ne $value) {
            $maxActiveAgents = [Math]::Max(1, [int]$value)
        }
    }

    return [pscustomobject]@{
        source = $(if ([string]::IsNullOrWhiteSpace($configPath)) { "" } else { Get-RelativePath -Path $configPath })
        enabled = $enabled
        immediateDispatch = $(if ($null -eq $activeProcessing) { $false } else { ConvertTo-Bool (Get-OptionalJsonProperty -Object $activeProcessing -Name "immediateDispatch") })
        noQueueDelay = $(if ($null -eq $activeProcessing) { $false } else { ConvertTo-Bool (Get-OptionalJsonProperty -Object $activeProcessing -Name "noQueueDelay") })
        standbyActivation = $(if ($null -eq $agentActivation) { $false } else { ConvertTo-Bool (Get-OptionalJsonProperty -Object $agentActivation -Name "standbyActivation") })
        maxActiveAgents = $maxActiveAgents
        mcpServerUrl = $(if ($null -eq $mcpIntegration) { "http://127.0.0.1:8787" } else { [string](Get-OptionalJsonProperty -Object $mcpIntegration -Name "serverUrl") })
    }
}

$status = Invoke-OrchestratorStatusSnapshot
$repoState = Get-RepoState
$activeConfig = Get-ActiveProcessingConfig
$dispatchOrder = Get-DispatchOrderMap
$parallelSlots = Get-EligibleParallelSlots -Status $status -DispatchOrderMap $dispatchOrder -MaxActiveAgents $activeConfig.maxActiveAgents
$blockedReasons = @(Get-BlockedReasons -RepoState $repoState -Status $status -ActiveProcessingEnabled $activeConfig.enabled)

$serviceHealth = Get-OptionalJsonProperty -Object $status -Name "serviceHealth"
$mcpCapability = $null
if ($null -ne $serviceHealth) {
    $mcpCapability = Get-OptionalJsonProperty -Object $serviceHealth -Name "mcpCapability"
}

$dispatchMode = "parallel_ready"
$nextAction = "Parallel fleet plan is ready."
if ($blockedReasons.Count -gt 0) {
    $dispatchMode = "hold_for_mcp_p0"
    $nextAction = "Finish dirty local MCP/control-plane P0 work before parallel activation."
}
elseif ($parallelSlots.selected.Count -eq 0) {
    $dispatchMode = "no_safe_slots"
    $nextAction = "No slot is currently safe to wake. Reconcile status/runtime blockers first."
}

$plan = [pscustomobject]@{
    ok = $true
    action = "active_agent_fleet_plan"
    generatedAt = (Get-Date).ToString("o")
    root = $Root
    outputPath = $OutputPath
    activeProcessing = $activeConfig
    repo = [pscustomobject]@{
        branch = [string]$repoState.branch
        gitAvailable = [bool]$repoState.gitAvailable
        dirty = [bool]$repoState.dirty
        changedCount = [int]$repoState.changedCount
        changedFiles = @($repoState.changedFiles | Select-Object status, path)
        controlPlaneDirtyFiles = @($repoState.controlPlaneDirtyFiles | Select-Object status, path)
        error = [string]$repoState.error
    }
    orchestratorStatus = [pscustomobject]@{
        state = [string](Get-OptionalJsonProperty -Object $status -Name "state")
        headline = [string](Get-OptionalJsonProperty -Object $status -Name "headline")
        queueRecommendation = Get-OptionalJsonProperty -Object $status -Name "queueRecommendation"
        nextAction = Get-OptionalJsonProperty -Object $status -Name "nextAction"
        availability = Get-OptionalJsonProperty -Object $status -Name "availability"
    }
    mcpLane = [pscustomobject]@{
        blocked = $blockedReasons.Count -gt 0
        blockedReasons = @($blockedReasons)
        capabilityMode = $(if ($null -eq $mcpCapability) { "" } else { [string](Get-OptionalJsonProperty -Object $mcpCapability -Name "mode") })
        writable = $(if ($null -eq $mcpCapability) { $false } else { ConvertTo-Bool (Get-OptionalJsonProperty -Object $mcpCapability -Name "writable") })
        nextAction = $nextAction
    }
    parallelPlan = [pscustomobject]@{
        dispatchMode = $dispatchMode
        candidateSlots = @($parallelSlots.candidates)
        selectedSlots = $(if ($dispatchMode -eq "parallel_ready") { @($parallelSlots.selected) } else { @() })
        futureSlotsAfterMcpFix = $(if ($dispatchMode -eq "parallel_ready") { @() } else { @($parallelSlots.selected) })
        maxActiveAgents = [int]$activeConfig.maxActiveAgents
    }
    nextAction = [pscustomobject]@{
        action = $nextAction
        owner = "Alex"
        when = "now"
        blockedBy = $(if ($blockedReasons.Count -gt 0) { $blockedReasons[0] } elseif ($parallelSlots.selected.Count -eq 0) { "no_safe_slots" } else { "none" })
    }
}

$plan.repo.changedFiles = ConvertTo-ArrayValue -Value $plan.repo.changedFiles
$plan.repo.controlPlaneDirtyFiles = ConvertTo-ArrayValue -Value $plan.repo.controlPlaneDirtyFiles
$plan.mcpLane.blockedReasons = ConvertTo-ArrayValue -Value $plan.mcpLane.blockedReasons
$plan.parallelPlan.candidateSlots = ConvertTo-ArrayValue -Value $plan.parallelPlan.candidateSlots
$plan.parallelPlan.selectedSlots = ConvertTo-ArrayValue -Value $plan.parallelPlan.selectedSlots
$plan.parallelPlan.futureSlotsAfterMcpFix = ConvertTo-ArrayValue -Value $plan.parallelPlan.futureSlotsAfterMcpFix

$outputDir = Split-Path -Parent $OutputPath
if (-not (Test-Path -LiteralPath $outputDir -PathType Container)) {
    New-Item -ItemType Directory -Force -Path $outputDir | Out-Null
}

$json = $plan | ConvertTo-Json -Depth 20
$json | Set-Content -LiteralPath $OutputPath -Encoding UTF8
Write-Output $json
