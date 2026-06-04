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

$serverScript = Join-Path $Root "scripts\Start-OrchMcpServer.ps1"
if (-not (Test-Path -LiteralPath $serverScript -PathType Leaf)) {
    throw "MCP server script was not found: $serverScript"
}

$toolsScript = Join-Path $Root "scripts\Start-OrchMcpServer.Tools.ps1"
if (-not (Test-Path -LiteralPath $toolsScript -PathType Leaf)) {
    throw "MCP server tools script was not found: $toolsScript"
}

$safeRunnerFixScript = Join-Path $Root "scripts\Start-OrchMcpServer.SafePowerShellRunnerFix.ps1"
if (-not (Test-Path -LiteralPath $safeRunnerFixScript -PathType Leaf)) {
    throw "MCP safe PowerShell runner fix script was not found: $safeRunnerFixScript"
}

$serverContent = Get-Content -LiteralPath $serverScript -Raw
$toolsContent = Get-Content -LiteralPath $toolsScript -Raw
$safeRunnerFixContent = Get-Content -LiteralPath $safeRunnerFixScript -Raw
$content = $serverContent + "`n" + $toolsContent + "`n" + $safeRunnerFixContent

function Assert-ContainsLiteral {
    param(
        [Parameter(Mandatory = $true)][string]$Needle,
        [Parameter(Mandatory = $true)][string]$Message
    )

    if ($content -notmatch [regex]::Escape($Needle)) {
        throw $Message
    }
}

Assert-ContainsLiteral `
    -Needle 'Invoke-OrchestratorSafePowerShell.ps1' `
    -Message 'MCP server must reference the audited safe PowerShell runner helper.'

Assert-ContainsLiteral `
    -Needle '$SafePowerShellRunnerScript' `
    -Message 'MCP server must define and use $SafePowerShellRunnerScript instead of an ad-hoc command path.'

Assert-ContainsLiteral `
    -Needle '$SafePowerShellRunnerFixScript' `
    -Message 'MCP server must define and load $SafePowerShellRunnerFixScript to override raw argument serialization.'

if ($serverContent -notmatch 'foreach\s*\(\s*\$requiredScript\s+in\s+@\([\s\S]*\$SafePowerShellRunnerScript') {
    throw 'MCP server startup required-script check must include $SafePowerShellRunnerScript.'
}

if ($serverContent -notmatch 'foreach\s*\(\s*\$requiredScript\s+in\s+@\([\s\S]*\$SafePowerShellRunnerFixScript') {
    throw 'MCP server startup required-script check must include $SafePowerShellRunnerFixScript.'
}

if ($serverContent -notmatch '\.\s+\$ToolsScript\s+[\s\S]*\.\s+\$SafePowerShellRunnerFixScript') {
    throw 'MCP server must dot-source $SafePowerShellRunnerFixScript after $ToolsScript so the corrected wrapper overrides the tools definition.'
}

Assert-ContainsLiteral `
    -Needle 'run_safe_powershell' `
    -Message 'MCP tools list and dispatch must expose the exact tool name run_safe_powershell.'

if ($content -notmatch 'name\s*=\s*"run_safe_powershell"') {
    throw 'Get-ToolsList must advertise a tool named exactly run_safe_powershell.'
}

if ($content -notmatch 'script_name') {
    throw 'run_safe_powershell schema must include a script_name argument.'
}

if ($safeRunnerFixContent -notmatch 'function\s+Get-StrictRunSafePowerShellSchema') {
    throw 'run_safe_powershell exported schema must be replaced by a strict connector-compatible schema helper.'
}

if ($safeRunnerFixContent -notmatch 'additionalProperties\s*=\s*\$false') {
    throw 'run_safe_powershell exported schema must set additionalProperties = $false.'
}

foreach ($name in @('script_name', 'argument_json', 'dry_run', 'plan_only', 'timeout_seconds')) {
    if ($safeRunnerFixContent -notmatch ('required\s*=\s*@\([\s\S]*"{0}"' -f [regex]::Escape($name))) {
        throw "run_safe_powershell exported schema required list must include $name."
    }
}

if ($safeRunnerFixContent -notmatch 'argument_json\s*=\s*\[pscustomobject\]@\{\s*type\s*=\s*"string"') {
    throw 'run_safe_powershell exported schema must expose argument_json as a flat string carrier.'
}

if ($safeRunnerFixContent -match '(?m)^\s*argument_json_base64\s*=\s*\[pscustomobject\]@') {
    throw 'run_safe_powershell exported schema must not expose argument_json_base64; use the flat argument_json string carrier.'
}

if ($safeRunnerFixContent -match '(?m)^\s*arguments\s*=\s*\[pscustomobject\]@') {
    throw 'run_safe_powershell exported schema must not expose raw arguments array/object carriers.'
}

if ($safeRunnerFixContent -match 'default\s*=') {
    throw 'run_safe_powershell exported schema must avoid defaults; apply defaults server-side.'
}

if ($safeRunnerFixContent -notmatch 'ConvertTo-Json\s+-InputObject\s+@\(\$rawArguments\)\s+-Depth\s+80\s+-Compress') {
    throw 'run_safe_powershell raw arguments runtime path must serialize the full array as one JSON value with ConvertTo-Json -InputObject @($rawArguments).'
}

if ($safeRunnerFixContent -match '\$rawArguments\s*\|\s*ConvertTo-Json') {
    throw 'run_safe_powershell raw arguments runtime path must not use pipeline ConvertTo-Json because it can emit multiple JSON primitives.'
}

if ($content -notmatch '"run_safe_powershell"\s*\{') {
    throw 'Invoke-ToolCall must dispatch the exact run_safe_powershell tool name.'
}

if ($content -notmatch 'Invoke-SafePowerShellRunnerTool') {
    throw 'run_safe_powershell dispatch must route through a dedicated Invoke-SafePowerShellRunnerTool wrapper.'
}

Write-Host 'Validated MCP safe PowerShell runner tool-list, dispatch, strict schema export, and raw argument serialization contract.'
