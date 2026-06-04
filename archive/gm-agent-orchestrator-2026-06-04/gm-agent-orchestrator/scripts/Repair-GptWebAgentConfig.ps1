<#
.SYNOPSIS
Safely repairs the local gpt-web slot binding in config/agents.json.

.DESCRIPTION
config/agents.json is local runtime configuration and may drift from the tracked
example. This helper patches only the gpt-web slot so it uses the browser-based
Start-GptWebAgent.ps1 runner instead of any Claude CLI command.

Default mode is dry-run. Pass -Apply to write the config. A timestamped backup
is created before writes.

.PARAMETER Root
Repository root. Defaults to the parent of scripts/.

.PARAMETER ConfigPath
Path to the local agents config. Defaults to config/agents.json under Root.

.PARAMETER Apply
Write the repaired config. Without this switch, prints the intended change only.

.EXAMPLE
.\scripts\Repair-GptWebAgentConfig.ps1

.EXAMPLE
.\scripts\Repair-GptWebAgentConfig.ps1 -Apply
#>

[CmdletBinding()]
param(
    [string]$Root = "",
    [string]$ConfigPath = "",
    [switch]$Apply
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-RepoRoot {
    param([string]$Value)

    if ([string]::IsNullOrWhiteSpace($Value)) {
        return (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
    }

    return (Resolve-Path $Value).Path
}

function New-GptWebSlot {
    return [pscustomobject]@{
        name = "gpt-web"
        agent = "gpt-web"
        role = "browser-fallback"
        enabled = $false
        branch = "agent/gpt-web"
        command = [pscustomobject]@{
            start = @(
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                "$task = '{task_path}'; if ([string]::IsNullOrWhiteSpace($task)) { throw 'Missing {task_path}; gpt-web requires an orchestrator-claimed active task.' }; $root = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $task)); & (Join-Path $root 'scripts\Start-GptWebAgent.ps1') -Root $root -MaxTasks 1 -TaskFile $task"
            )
            resume = @(
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                "$task = '{task_path}'; if ([string]::IsNullOrWhiteSpace($task)) { throw 'Missing {task_path}; gpt-web requires an orchestrator-claimed active task.' }; $root = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $task)); & (Join-Path $root 'scripts\Start-GptWebAgent.ps1') -Root $root -MaxTasks 1 -TaskFile $task"
            )
        }
    }
}

function ConvertTo-OrderedJson {
    param([Parameter(Mandatory = $true)]$Value)
    return ($Value | ConvertTo-Json -Depth 30)
}

$repoRoot = Resolve-RepoRoot -Value $Root
if ([string]::IsNullOrWhiteSpace($ConfigPath)) {
    $ConfigPath = Join-Path $repoRoot "config\agents.json"
}
elseif (-not [System.IO.Path]::IsPathRooted($ConfigPath)) {
    $ConfigPath = Join-Path $repoRoot $ConfigPath
}

if (-not (Test-Path -LiteralPath $ConfigPath -PathType Leaf)) {
    throw "Local agents config not found: $ConfigPath. Create it from config\agents.example.json first."
}

$config = Get-Content -LiteralPath $ConfigPath -Raw -Encoding UTF8 | ConvertFrom-Json
if ($null -eq $config.PSObject.Properties["slots"]) {
    throw "Invalid agents config: missing slots array."
}

$slots = @($config.slots)
$existing = $slots | Where-Object { [string]$_.name -eq "gpt-web" } | Select-Object -First 1
$replacement = New-GptWebSlot
$action = "add"
$preservedEnabled = $false

if ($null -ne $existing) {
    $action = "replace"
    if ($null -ne $existing.PSObject.Properties["enabled"]) {
        $preservedEnabled = [bool]$existing.enabled
        $replacement.enabled = $preservedEnabled
    }

    $slots = @($slots | Where-Object { [string]$_.name -ne "gpt-web" })
}

$config.slots = @($slots + $replacement)

$afterJson = ConvertTo-OrderedJson -Value $config
$beforeJson = Get-Content -LiteralPath $ConfigPath -Raw -Encoding UTF8
$changed = ($beforeJson.Trim() -ne $afterJson.Trim())

$result = [pscustomobject]@{
    ok = $true
    dryRun = -not [bool]$Apply
    configPath = $ConfigPath
    action = $action
    changed = $changed
    preservedEnabled = $preservedEnabled
    gptWebCommand = $replacement.command.start
    backupPath = $null
    nextAction = if ($Apply) { "Run a parser/config check, then dry-run the gpt-web slot before dispatch." } else { "Review this plan, then rerun with -Apply to update config\agents.json." }
}

if (-not $changed) {
    $result.nextAction = "No change needed. gpt-web already uses the independent Start-GptWebAgent.ps1 binding."
    $result | ConvertTo-Json -Depth 20
    exit 0
}

if ($Apply) {
    $backupPath = "{0}.bak-gpt-web-{1}" -f $ConfigPath, (Get-Date -Format "yyyyMMdd-HHmmss")
    Copy-Item -LiteralPath $ConfigPath -Destination $backupPath -Force
    Set-Content -LiteralPath $ConfigPath -Value ($afterJson + "`n") -Encoding UTF8
    $result.backupPath = $backupPath
}

$result | ConvertTo-Json -Depth 20
