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

$toolsScript = Join-Path $Root "scripts\Start-OrchMcpServer.Tools.ps1"
$restartScript = Join-Path $Root "scripts\Restart-OrchMcpServer.ps1"

foreach ($path in @($toolsScript, $restartScript)) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Required MCP ops file is missing: $path"
    }
}

$Port = 8787
$NoAuth = $true
. $toolsScript

$tools = @((Get-ToolsList).tools)

function Get-Tool {
    param([string]$Name)
    return @($tools | Where-Object { $_.name -eq $Name } | Select-Object -First 1)
}

$runner = Get-Tool -Name "run_safe_powershell"
if ($null -eq $runner) { throw "tools/list must include run_safe_powershell." }
if ($runner.inputSchema.properties.arguments.type -ne "array") { throw "run_safe_powershell arguments must be an array." }
if ($runner.inputSchema.properties.arguments.items.type -ne "string") { throw "run_safe_powershell arguments array must declare string items." }

$restart = Get-Tool -Name "restart_mcp_server"
if ($null -eq $restart) { throw "tools/list must include restart_mcp_server." }
if (@($restart.inputSchema.required) -notcontains "reason") { throw "restart_mcp_server must require a reason." }
if ($restart.inputSchema.properties.dry_run.default -ne $true) { throw "restart_mcp_server must default dry_run to true." }
if ($restart.inputSchema.properties.port.default -ne 8787) { throw "restart_mcp_server must default to MCP port 8787." }

$supervisor = Get-Tool -Name "run_service_supervisor"
if ($null -eq $supervisor) { throw "tools/list must include run_service_supervisor." }
if ($supervisor.inputSchema.properties.dry_run.default -ne $true) { throw "run_service_supervisor must default dry_run to true." }

$canary = Get-Tool -Name "get_tunnel_canary_status"
if ($null -eq $canary) { throw "tools/list must include get_tunnel_canary_status." }

$fleetPlan = Get-Tool -Name "get_active_fleet_plan"
if ($null -eq $fleetPlan) { throw "tools/list must include get_active_fleet_plan." }

$overview = Get-Tool -Name "get_mcp_feature_overview"
if ($null -eq $overview) { throw "tools/list must include get_mcp_feature_overview." }

$overviewResult = Get-McpFeatureOverviewTool
if (@($overviewResult.groups.powershellOps) -notcontains "run_safe_powershell") { throw "Feature overview must list run_safe_powershell under powershellOps." }
if (@($overviewResult.groups.serviceOps) -notcontains "restart_mcp_server") { throw "Feature overview must list restart_mcp_server under serviceOps." }
if (@($overviewResult.groups.serviceOps) -notcontains "get_tunnel_canary_status") { throw "Feature overview must list get_tunnel_canary_status under serviceOps." }
if (@($overviewResult.groups.serviceOps) -notcontains "get_active_fleet_plan") { throw "Feature overview must list get_active_fleet_plan under serviceOps." }
if (@($overviewResult.missingOpsGaps) -notcontains "hold_task") { throw "Feature overview must list hold_task as a missing ops gap." }
# commit_staged_changes is now implemented — assert it is in gitAndGitHubOps, not missingOpsGaps.
if (@($overviewResult.groups.gitAndGitHubOps) -notcontains "commit_staged_changes") { throw "Feature overview must list commit_staged_changes under gitAndGitHubOps (it is now implemented)." }
if (@($overviewResult.missingOpsGaps) -contains "commit_staged_changes") { throw "Feature overview must NOT list commit_staged_changes as a missing gap (it is implemented)." }

$toolsContent = Get-Content -LiteralPath $toolsScript -Raw
if ($toolsContent -notmatch '"get_recent_failures"\s*\{[\s\S]*Get-OptionalJsonProperty\s+-Object\s+\$Arguments\s+-Name\s+"limit"') {
    throw "get_recent_failures must read optional limit through Get-OptionalJsonProperty."
}
if ($toolsContent -match 'function\s+Get-TunnelCanaryStatusTool\s*\{\s*return\s+Invoke-JsonScript\s+-ScriptPath\s+\$TunnelCanaryScript') {
    throw "get_tunnel_canary_status must not self-probe the same MCP listener in-band."
}
if ($toolsContent -notmatch 'in_band_mcp_self_probe_deadlock_risk') {
    throw "get_tunnel_canary_status must return an explicit in-band deadlock warning."
}

$restartContent = Get-Content -LiteralPath $restartScript -Raw
if ($restartContent -notmatch 'Get-CimInstance Win32_Process') { throw "Restart helper must inspect process identity before stopping anything." }
if ($restartContent -notmatch '\$serverNamePattern') { throw "Restart helper must use a bounded server script basename matcher." }
if ($restartContent -notmatch '\$isServer\s*=\s*\(\$commandLine\s+-match\s+\$escapedServer\)\s+-or\s+\(\$commandLine\s+-match\s+\$serverNamePattern\)') { throw "Restart helper must require the MCP server script identity in the process command line." }
if ($restartContent -notmatch '\$commandLine\s+-match\s+"\(\?i\)\(\^') { throw "Restart helper must inspect explicit -Port arguments when present." }
if ($restartContent -notmatch 'return\s+\(\$Port\s+-eq\s+8787\)') { throw "Restart helper must only treat omitted -Port as the default MCP port." }
if ($restartContent -notmatch 'Start-Process[\s\S]*-WindowStyle Hidden') { throw "Restart helper must schedule detached hidden restart work." }
if ($restartContent -match 'Cold-Start\.ps1') { throw "Restart helper must not route through Cold-Start.ps1." }

$tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("orch-mcp-restart-test-{0}" -f [Guid]::NewGuid().ToString("N"))
try {
    New-Item -ItemType Directory -Force -Path (Join-Path $tempRoot "scripts") | Out-Null
    "Write-Host 'dummy server'" | Set-Content -LiteralPath (Join-Path $tempRoot "scripts\Start-OrchMcpServer.ps1") -Encoding UTF8

    $output = & powershell -NoProfile -ExecutionPolicy Bypass -File $restartScript -Root $tempRoot -Reason "contract dry run" -DryRun 2>&1
    if ($LASTEXITCODE -ne 0) { throw "Restart helper dry run failed: $($output -join "`n")" }
    $result = ($output -join "`n") | ConvertFrom-Json -ErrorAction Stop
    if ($result.ok -ne $true) { throw "Restart helper dry run must report ok=true." }
    if ($result.dryRun -ne $true) { throw "Restart helper dry run must report dryRun=true." }
    if ($result.workerProcessId -ne $null) { throw "Restart helper dry run must not schedule a worker process." }
    if ($result.healthUrl -ne "http://127.0.0.1:8787/health") { throw "Restart helper dry run must report the expected health URL." }
}
finally {
    Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host "Validated MCP ops feature and restart tool contracts."
