[CmdletBinding()]
param(
    [string]$Root = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Root)) {
    $scriptDir = if (-not [string]::IsNullOrWhiteSpace($PSScriptRoot)) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Path }
    $Root = (Resolve-Path (Join-Path $scriptDir "..")).Path
}
else {
    $Root = (Resolve-Path $Root).Path
}

$patcher = Join-Path $Root "scripts\Patch-OrchMcpSafeTools.ps1"
$server = Join-Path $Root "scripts\Start-OrchMcpServer.ps1"
$tools = Join-Path $Root "scripts\Start-OrchMcpServer.Tools.ps1"
$safeRunner = Join-Path $Root "scripts\Invoke-OrchestratorSafePowerShell.ps1"
$queueHelper = Join-Path $Root "scripts\New-OrchestratorQueueTask.ps1"

foreach ($path in @($patcher, $server, $tools, $safeRunner, $queueHelper)) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Required MCP safe-tool file is missing: $path"
    }
}

$patcherContent = Get-Content -LiteralPath $patcher -Raw
$toolsContent = Get-Content -LiteralPath $tools -Raw
foreach ($needle in @(
    'Invoke-OrchestratorSafePowerShell.ps1',
    'New-OrchestratorQueueTask.ps1',
    '$SafePowerShellRunnerScript',
    '$QueueTaskCreateScript',
    'function Invoke-SafePowerShellRunnerTool',
    'function Invoke-CreateQueueTaskTool',
    'run_safe_powershell',
    'create_queue_task',
    '-ArgumentJson',
    'blocked_by',
    'ParseInput'
)) {
    if ($patcherContent -notmatch [regex]::Escape($needle)) {
        throw "Patch-OrchMcpSafeTools.ps1 must preserve MCP safe-tool patch contract: missing $needle"
    }
}

$safeRunnerContent = Get-Content -LiteralPath $safeRunner -Raw
if ($safeRunnerContent -notmatch [regex]::Escape('New-OrchestratorQueueTask.ps1')) {
    throw 'Safe runner allowlist must include New-OrchestratorQueueTask.ps1 for create_queue_task fallback and audited queue creation.'
}

if ($patcherContent -match '[\"'']-Arguments[\"'']') {
    throw 'run_safe_powershell MCP wrapper must forward raw arguments through -ArgumentJson or -RunnerArguments, not -Arguments.'
}

if ($toolsContent -match '[\"'']-Arguments[\"'']') {
    throw 'run_safe_powershell MCP wrapper must not pass raw connector arguments through unsupported -Arguments.'
}

if ($toolsContent -notmatch '\$null\s+-eq\s+\$dryRun[\s\S]*\$args\s+\+=\s+"-DryRun"') {
    throw 'create_queue_task must default to dry-run when dry_run is omitted.'
}

$output = & powershell -NoProfile -ExecutionPolicy Bypass -File $patcher -Root $Root -DryRun 2>&1
if ($LASTEXITCODE -ne 0) {
    throw "Patch-OrchMcpSafeTools.ps1 -DryRun failed: $($output -join "`n")"
}

try { $result = ($output -join "`n") | ConvertFrom-Json -ErrorAction Stop }
catch { throw "Patch-OrchMcpSafeTools.ps1 -DryRun emitted invalid JSON: $($_.Exception.Message). Output: $($output -join "`n")" }

if ($result.ok -ne $true) { throw 'Patch-OrchMcpSafeTools.ps1 -DryRun must report ok=true.' }
if (@($result.wiredTools) -notcontains 'run_safe_powershell') { throw 'Patch dry run must report run_safe_powershell as a wired tool.' }
if (@($result.wiredTools) -notcontains 'create_queue_task') { throw 'Patch dry run must report create_queue_task as a wired tool.' }

Write-Host 'Validated MCP safe-tool patch contract.'
