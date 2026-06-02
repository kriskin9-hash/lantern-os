[CmdletBinding()]
param(
    [string]$Root = "",
    [string]$AgentsConfigPath = "",
    [string]$ProfilesConfigPath = "",
    [string]$BindingsConfigPath = "",
    [switch]$WriteStatus,
    [switch]$FixRecommendations
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Root)) {
    $Root = (Resolve-Path "$PSScriptRoot\..").Path
}
else {
    $Root = (Resolve-Path $Root).Path
}

if ([string]::IsNullOrWhiteSpace($AgentsConfigPath)) {
    $AgentsConfigPath = Join-Path $Root "config\agents.json"
}
if ([string]::IsNullOrWhiteSpace($ProfilesConfigPath)) {
    $ProfilesConfigPath = Join-Path $Root "config\agent-profiles.json"
}
if ([string]::IsNullOrWhiteSpace($BindingsConfigPath)) {
    $BindingsConfigPath = Join-Path $Root "config\slot-bindings.json"
}

function Read-JsonRequired {
    param([string]$Path)
    if (!(Test-Path $Path)) { throw "Missing required JSON config: $Path" }
    return Get-Content $Path -Raw | ConvertFrom-Json
}

function Add-Finding {
    param(
        [System.Collections.Generic.List[object]]$Findings,
        [string]$Severity,
        [string]$Code,
        [string]$Message,
        [string]$Step = ""
    )
    $Findings.Add([pscustomobject]@{
        severity = $Severity
        code = $Code
        message = $Message
        step = $Step
    }) | Out-Null
}

$findings = New-Object System.Collections.Generic.List[object]
$agents = Read-JsonRequired $AgentsConfigPath
$profiles = Read-JsonRequired $ProfilesConfigPath
$bindings = Read-JsonRequired $BindingsConfigPath

# --- Diversity metrics ---
$agentCounts = @{}
$stepAgents = @{}
$enabledSlots = @($agents.slots | Where-Object { $_.enabled })

foreach ($slot in $enabledSlots) {
    $agent = [string]$slot.agent
    $step = [int]$slot.step

    # Count per agent type
    if (-not $agentCounts.ContainsKey($agent)) { $agentCounts[$agent] = 0 }
    $agentCounts[$agent]++

    # Track agents per step
    if (-not $stepAgents.ContainsKey($step)) { $stepAgents[$step] = New-Object System.Collections.Generic.HashSet[string] }
    $stepAgents[$step].Add($agent) | Out-Null
}

$totalSlots = $enabledSlots.Count
$uniqueAgentTypes = $agentCounts.Keys.Count
$targetAgentTypes = 4  # claude, codex, gemini, devin
$idealPerAgent = if ($totalSlots -gt 0) { $totalSlots / $targetAgentTypes } else { 0 }

# --- Check 1: Agent type count ---
if ($uniqueAgentTypes -lt 2) {
    Add-Finding $findings "error" "fleet_monoculture" "Fleet has only $uniqueAgentTypes agent type(s). Minimum healthy diversity = 2. Target = $targetAgentTypes."
}
elseif ($uniqueAgentTypes -lt $targetAgentTypes) {
    Add-Finding $findings "warning" "fleet_under_diversity" "Fleet has $uniqueAgentTypes agent types. Target = $targetAgentTypes (claude, codex, gemini, devin)."
}

# --- Check 2: Even distribution ---
foreach ($agent in $agentCounts.Keys) {
    $count = $agentCounts[$agent]
    $ratio = if ($totalSlots -gt 0) { $count / $totalSlots } else { 0 }
    if ($ratio -gt 0.40) {
        Add-Finding $findings "warning" "agent_imbalanced" "Agent '$agent' holds $(($ratio*100).ToString('F0'))% of slots ($count/$totalSlots). Ideal = ~$(($idealPerAgent/$totalSlots*100).ToString('F0'))%."
    }
}

# --- Check 3: Step-level diversity ---
for ($step = 1; $step -le 12; $step++) {
    if (-not $stepAgents.ContainsKey($step)) {
        Add-Finding $findings "error" "step_empty" "Step $step has no enabled slots." -Step "$step"
        continue
    }
    $stepCount = $stepAgents[$step].Count
    if ($stepCount -lt 2) {
        Add-Finding $findings "error" "step_monoculture" "Step $step has only $stepCount agent type(s). Each step needs >=2 for redundancy." -Step "$step"
    }
    elseif ($stepCount -lt 3) {
        Add-Finding $findings "warning" "step_under_diversity" "Step $step has $stepCount agent types. Ideal = 3 per step." -Step "$step"
    }
}

# --- Check 4: Command specs present for enabled slots ---
$slotsMissingCommand = 0
foreach ($slot in $enabledSlots) {
    $cmd = @($slot.command.start)
    if ($cmd.Count -eq 0 -or [string]::IsNullOrWhiteSpace([string]$cmd[0])) {
        $slotsMissingCommand++
    }
}
if ($slotsMissingCommand -gt 0) {
    Add-Finding $findings "error" "slots_missing_command" "$slotsMissingCommand enabled slot(s) have no command.start. Agents cannot execute tasks without a CLI command."
}

# --- Check 5: Branch uniqueness (per-step isolation) ---
$branchSet = New-Object System.Collections.Generic.HashSet[string]
$duplicateBranches = @()
foreach ($slot in $enabledSlots) {
    $branch = [string]$slot.branch
    if (-not $branchSet.Add($branch)) {
        $duplicateBranches += $slot.name
    }
}
if ($duplicateBranches.Count -gt 0) {
    Add-Finding $findings "warning" "branch_collision" "$( $duplicateBranches.Count ) slot(s) share branches: $( ($duplicateBranches | Select-Object -First 5) -join ', ' ) ..."
}

# --- Check 6: Profile binding coverage ---
$bindingSlotNames = New-Object System.Collections.Generic.HashSet[string]
foreach ($b in $bindings.slots) { $bindingSlotNames.Add([string]$b.slot) | Out-Null }
foreach ($slot in $enabledSlots) {
    $name = [string]$slot.name
    if (-not $bindingSlotNames.Contains($name)) {
        Add-Finding $findings "error" "slot_unbound" "Slot '$name' has no profile binding in slot-bindings.json."
    }
}

# --- Check 7: Profile env var readiness ---
$profileById = @{}
foreach ($p in $profiles.profiles) { $profileById[[string]$p.id] = $p }

$missingEnvProfiles = @()
foreach ($binding in $bindings.slots) {
    $profile = $profileById[[string]$binding.profileId]
    if ($null -eq $profile) { continue }
    $missing = @()
    foreach ($var in @($profile.requiredEnvVars)) {
        if ([string]::IsNullOrWhiteSpace([Environment]::GetEnvironmentVariable($var))) {
            $missing += $var
        }
    }
    if ($missing.Count -gt 0) {
        $missingEnvProfiles += "$( $binding.profileId ) needs: $( $missing -join ', ' )"
    }
}
if ($missingEnvProfiles.Count -gt 0) {
    $uniqueMissing = ($missingEnvProfiles | Select-Object -Unique)
    Add-Finding $findings "warning" "env_vars_missing" "Some profiles lack env vars: $( ($uniqueMissing | Select-Object -First 3) -join '; ' )"
}

# --- Diversity score ---
$maxDiversityScore = 100
$deductions = 0
foreach ($f in $findings) {
    switch ($f.severity) {
        "error"   { $deductions += 15 }
        "warning" { $deductions += 5 }
    }
}
$diversityScore = [Math]::Max(0, $maxDiversityScore - $deductions)
$health = if ($diversityScore -ge 90) { "healthy" } elseif ($diversityScore -ge 70) { "degraded" } else { "critical" }

# --- Recommendations ---
$recommendations = @()
if ($uniqueAgentTypes -lt $targetAgentTypes) {
    $missingAgents = @("claude","codex","gemini","devin") | Where-Object { -not $agentCounts.ContainsKey($_) }
    if ($missingAgents.Count -gt 0) {
        $recommendations += "Add agent profiles for: $( $missingAgents -join ', ' )"
    }
}
if ($slotsMissingCommand -gt 0) {
    $recommendations += "Populate command.start for all enabled slots so agents can execute."
}
if ($duplicateBranches.Count -gt 0) {
    $recommendations += "Assign unique branches to each slot for git worktree isolation."
}
if ($health -eq "healthy" -and $findings.Count -eq 0) {
    $recommendations += "Fleet diversity is excellent. Run Start-ActiveAgentFleet.ps1 to wake slots."
}

# --- Build status ---
$status = [pscustomobject]@{
    generatedAt = (Get-Date).ToString("o")
    root = $Root
    agentsConfigPath = $AgentsConfigPath
    profilesConfigPath = $ProfilesConfigPath
    bindingsConfigPath = $BindingsConfigPath
    totalSlots = $totalSlots
    enabledSlots = $enabledSlots.Count
    uniqueAgentTypes = $uniqueAgentTypes
    agentDistribution = $agentCounts
    stepDiversity = @{}
    diversityScore = $diversityScore
    health = $health
    findingCount = $findings.Count
    findings = @($findings)
    recommendations = @($recommendations)
}

for ($s = 1; $s -le 12; $s++) {
    if ($stepAgents.ContainsKey($s)) {
        $status.stepDiversity["$s"] = @($stepAgents[$s])
    }
    else {
        $status.stepDiversity["$s"] = @()
    }
}

if ($WriteStatus) {
    $statusDir = Join-Path $Root "status"
    New-Item -ItemType Directory -Force -Path $statusDir | Out-Null
    $status | ConvertTo-Json -Depth 10 | Set-Content -Path (Join-Path $statusDir "agent-fleet-diversity.json") -Encoding UTF8
}

# --- Console output ---
Write-Host ""
Write-Host "=== Agent Fleet Diversity Report ===" -ForegroundColor Cyan
Write-Host "Generated: $( $status.generatedAt )"
Write-Host "Total slots: $( $status.totalSlots ) | Enabled: $( $status.enabledSlots )"
Write-Host "Unique agent types: $( $status.uniqueAgentTypes )"
Write-Host ""
Write-Host "Agent Distribution:" -ForegroundColor Yellow
foreach ($kv in $agentCounts.GetEnumerator() | Sort-Object Value -Descending) {
    $bar = "█" * [Math]::Min(20, [int]($kv.Value / $totalSlots * 40))
    Write-Host "  $( $kv.Key.PadRight(10) ) $( $kv.Value.ToString().PadLeft(2) ) / $totalSlots  $bar"
}
Write-Host ""
Write-Host "Step-Level Diversity:" -ForegroundColor Yellow
for ($s = 1; $s -le 12; $s++) {
    $agentsInStep = if ($stepAgents.ContainsKey($s)) { @($stepAgents[$s]) } else { @() }
    $color = if ($agentsInStep.Count -ge 3) { "Green" } elseif ($agentsInStep.Count -ge 2) { "Yellow" } else { "Red" }
    Write-Host ("  Step {0:D2}: {1} agent type(s) — {2}" -f $s, $agentsInStep.Count, ($agentsInStep -join ", ")) -ForegroundColor $color
}
Write-Host ""
Write-Host "Diversity Score: $( $status.diversityScore ) / 100  [$( $status.health.ToUpper() )]" -ForegroundColor $(if($health -eq "healthy"){"Green"}elseif($health -eq "degraded"){"Yellow"}else{"Red"})
Write-Host "Findings: $( $status.findingCount )"
foreach ($f in $findings | Sort-Object severity) {
    $color = switch ($f.severity) { "error" { "Red" } "warning" { "Yellow" } default { "Gray" } }
    $stepLabel = if ($f.step) { " [step $( $f.step )]" } else { "" }
    Write-Host "  [$( $f.severity.ToUpper() )]$( $stepLabel ) $( $f.code ): $( $f.message )" -ForegroundColor $color
}
Write-Host ""
if ($recommendations.Count -gt 0) {
    Write-Host "Recommendations:" -ForegroundColor Cyan
    foreach ($r in $recommendations) { Write-Host "  - $r" }
    Write-Host ""
}

# --- JSON output ---
$status | ConvertTo-Json -Depth 10

if ($health -eq "critical") { exit 2 }
if ($health -eq "degraded") { exit 1 }
exit 0
