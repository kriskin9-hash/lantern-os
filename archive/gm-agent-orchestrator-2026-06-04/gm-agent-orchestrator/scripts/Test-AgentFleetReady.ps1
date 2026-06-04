[CmdletBinding()]
param(
    [string]$Root = "",
    [string]$AgentsConfigPath = "",
    [string]$MachinesConfigPath = "",
    [switch]$WriteStatus
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

if ([string]::IsNullOrWhiteSpace($MachinesConfigPath)) {
    $localMachines = Join-Path $Root "config\machines.json"
    $exampleMachines = Join-Path $Root "config\machines.example.json"
    $MachinesConfigPath = if (Test-Path $localMachines) { $localMachines } else { $exampleMachines }
}

function Read-JsonRequired {
    param([string]$Path)

    if (!(Test-Path $Path)) {
        throw "Missing required JSON config: $Path"
    }

    return Get-Content $Path -Raw | ConvertFrom-Json
}

function Add-Problem {
    param(
        [System.Collections.Generic.List[object]]$Problems,
        [string]$Severity,
        [string]$Code,
        [string]$Message
    )

    $Problems.Add([pscustomobject]@{
        severity = $Severity
        code = $Code
        message = $Message
    }) | Out-Null
}

$problems = New-Object System.Collections.Generic.List[object]
$agents = Read-JsonRequired $AgentsConfigPath
$machines = Read-JsonRequired $MachinesConfigPath

$slotNames = New-Object System.Collections.Generic.HashSet[string]
foreach ($slot in @($agents.slots)) {
    $name = [string]$slot.name
    if ([string]::IsNullOrWhiteSpace($name)) {
        Add-Problem $problems "error" "slot_name_missing" "A slot is missing a name."
        continue
    }

    if (-not $slotNames.Add($name)) {
        Add-Problem $problems "error" "slot_name_duplicate" "Duplicate slot name: $name"
    }

    if ($slot.enabled) {
        $command = @($slot.command.start)
        if ($command.Count -eq 0 -or [string]::IsNullOrWhiteSpace([string]$command[0])) {
            Add-Problem $problems "error" "slot_command_missing" "Enabled slot $name has no start command."
        }
        else {
            $exe = [string]$command[0]
            if (!(Get-Command $exe -ErrorAction SilentlyContinue)) {
                Add-Problem $problems "error" "slot_executable_missing" "Enabled slot $name executable not found on PATH: $exe"
            }
        }

        if ([string]::IsNullOrWhiteSpace([string]$slot.branch)) {
            Add-Problem $problems "error" "slot_branch_missing" "Enabled slot $name has no unique branch."
        }
    }
}

$machineSlotNames = New-Object System.Collections.Generic.HashSet[string]
foreach ($slot in @($machines.slots)) {
    $name = [string]$slot.name
    if ([string]::IsNullOrWhiteSpace($name)) {
        Add-Problem $problems "error" "machine_slot_name_missing" "A machine slot mapping is missing a name."
        continue
    }

    if (-not $machineSlotNames.Add($name)) {
        Add-Problem $problems "error" "machine_slot_duplicate" "Duplicate machine slot mapping: $name"
    }

    if (-not $slotNames.Contains($name)) {
        Add-Problem $problems "warning" "machine_slot_not_in_agents" "Machine slot $name does not exist in agents config."
    }
}

foreach ($name in $slotNames) {
    if (-not $machineSlotNames.Contains($name)) {
        Add-Problem $problems "warning" "agent_slot_missing_machine_metadata" "Agent slot $name has no machine metadata."
    }
}

if ([string]::IsNullOrWhiteSpace([string]$machines.machineId)) {
    Add-Problem $problems "error" "machine_id_missing" "Machine config is missing machineId."
}

if ([string]::IsNullOrWhiteSpace([string]$machines.trustTier)) {
    Add-Problem $problems "error" "trust_tier_missing" "Machine config is missing trustTier."
}

if ($machines.remoteWorkerRules -and $machines.remoteWorkerRules.forbidSharedNetworkWorktrees -ne $true) {
    Add-Problem $problems "warning" "shared_worktree_rule_not_enforced" "remoteWorkerRules.forbidSharedNetworkWorktrees should be true."
}

$status = [pscustomobject]@{
    generatedAt = (Get-Date).ToString("o")
    root = $Root
    agentsConfigPath = $AgentsConfigPath
    machinesConfigPath = $MachinesConfigPath
    machineId = $machines.machineId
    trustTier = $machines.trustTier
    slotCount = @($agents.slots).Count
    problemCount = $problems.Count
    problems = @($problems)
    ready = (@($problems | Where-Object { $_.severity -eq "error" }).Count -eq 0)
}

if ($WriteStatus) {
    $statusDir = Join-Path $Root "status"
    New-Item -ItemType Directory -Force -Path $statusDir | Out-Null
    $status | ConvertTo-Json -Depth 10 | Set-Content -Path (Join-Path $statusDir "agent-fleet-ready.json") -Encoding UTF8
}

$status | ConvertTo-Json -Depth 10

if (-not $status.ready) {
    exit 1
}
