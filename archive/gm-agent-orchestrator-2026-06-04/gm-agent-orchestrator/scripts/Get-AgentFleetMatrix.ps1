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

function Read-JsonOrNull {
    param([string]$Path)
    if (!(Test-Path $Path)) { return $null }
    try { return Get-Content $Path -Raw | ConvertFrom-Json }
    catch { return $null }
}

function Test-EnvPresence {
    param([string[]]$Names)
    $rows = @()
    foreach ($name in @($Names)) {
        $value = [Environment]::GetEnvironmentVariable($name)
        $rows += [pscustomobject]@{
            name = $name
            present = -not [string]::IsNullOrWhiteSpace([string]$value)
        }
    }
    return @($rows)
}

$agentsCfg = Read-JsonOrNull -Path (Join-Path $Root "config\agents.json")
$profilesCfg = Read-JsonOrNull -Path (Join-Path $Root "config\agent-profiles.json")
$bindingsCfg = Read-JsonOrNull -Path (Join-Path $Root "config\slot-bindings.json")

if ($null -eq $agentsCfg) { throw "Missing or invalid config\\agents.json" }
if ($null -eq $profilesCfg) { throw "Missing or invalid config\\agent-profiles.json" }
if ($null -eq $bindingsCfg) { throw "Missing or invalid config\\slot-bindings.json" }

$status = & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Root "scripts\Get-OrchestratorStatus.ps1") -Root $Root | Out-String | ConvertFrom-Json

$rows = @()
foreach ($slot in @($agentsCfg.slots)) {
    $binding = @($bindingsCfg.slots | Where-Object { $_.slot -eq $slot.name } | Select-Object -First 1)
    $binding = if ($binding.Count -gt 0) { $binding[0] } else { $null }
    $profile = $null
    if ($null -ne $binding -and -not [string]::IsNullOrWhiteSpace([string]$binding.profileId)) {
        $p = @($profilesCfg.profiles | Where-Object { $_.id -eq $binding.profileId } | Select-Object -First 1)
        if ($p.Count -gt 0) { $profile = $p[0] }
    }
    $runtime = @($status.slots | Where-Object { $_.name -eq $slot.name } | Select-Object -First 1)
    $runtime = if ($runtime.Count -gt 0) { $runtime[0] } else { $null }

    $binary = Get-Command $slot.agent -ErrorAction SilentlyContinue
    $worktreePath = if ($null -ne $binding) { [string]$binding.worktree } else { "" }
    $worktreeExists = $false
    if (-not [string]::IsNullOrWhiteSpace($worktreePath)) { $worktreeExists = Test-Path $worktreePath }

    $envChecks = @()
    if ($null -ne $profile) { $envChecks = Test-EnvPresence -Names @($profile.requiredEnvVars) }
    $envReady = $true
    if (@($envChecks).Count -gt 0) {
        $envReady = @($envChecks | Where-Object { -not $_.present }).Count -eq 0
    }

    $rows += [pscustomobject]@{
        slot = [string]$slot.name
        agent = [string]$slot.agent
        enabled = [bool]$slot.enabled
        role = [string]$slot.role
        profileId = $(if ($null -ne $binding) { [string]$binding.profileId } else { "" })
        provider = $(if ($null -ne $profile) { [string]$profile.provider } else { "" })
        taskBudget = $(if ($null -ne $profile) { [string]$profile.taskBudget } else { "" })
        binaryFound = ($null -ne $binary)
        binaryPath = $(if ($null -ne $binary) { [string]$binary.Source } else { "" })
        worktreeExists = $worktreeExists
        runtimeState = $(if ($null -ne $runtime) { [string]$runtime.state } else { "unknown" })
        runtimeNextAction = $(if ($null -ne $runtime) { [string]$runtime.nextAction.action } else { "unknown" })
        envReady = $envReady
        envChecks = @($envChecks)
    }
}

[pscustomobject]@{
    generatedAt = (Get-Date).ToString("o")
    root = $Root
    counts = $status.counts
    slots = @($rows)
} | ConvertTo-Json -Depth 20
