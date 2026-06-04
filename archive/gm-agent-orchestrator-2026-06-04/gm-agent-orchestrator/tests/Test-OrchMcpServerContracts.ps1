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

$serverScript = Join-Path $Root "scripts/Start-OrchMcpServer.ps1"
if (!(Test-Path $serverScript)) {
    throw "MCP server script was not found: $serverScript"
}

$toolsScript = Join-Path $Root "scripts/Start-OrchMcpServer.Tools.ps1"
if (!(Test-Path $toolsScript)) {
    throw "MCP server tools script was not found: $toolsScript"
}

$serverContent = Get-Content $serverScript -Raw
$toolsContent = Get-Content $toolsScript -Raw
$content = $serverContent + "`n" + $toolsContent

foreach ($toolName in @(
    "get_agent_status",
    "get_queue_summary",
    "get_recent_failures",
    "get_latest_agent_logs",
    "get_mcp_capability_status",
    "get_mcp_feature_overview",
    "get_tunnel_canary_status",
    "get_active_fleet_plan",
    "sync_repository",
    "requeue_task",
    "fail_task",
    "complete_task",
    "start_agent",
    "rerun_agent",
    "restart_mcp_server",
    "run_service_supervisor",
    "get_ibkr_quotes",
    "get_ibkr_orderbook",
    "get_ibkr_positions",
    "get_ibkr_account_risk",
    "get_spread_execution_readiness",
    "get_spread_profitability_snapshot",
    "plan_spread_live_micro_experiment",
    "get_live_steering_state",
    "steer_live_spread_trade",
    "get_spread_operator_packet"
)) {
    if ($content -notmatch [regex]::Escape($toolName)) {
        throw "MCP server is missing expected tool route: $toolName"
    }
}

foreach ($helper in @(
    "Get-OrchMcpCapabilityStatus.ps1",
    "Invoke-OrchestratorRepoSync.ps1",
    "Invoke-OrchestratorTaskAction.ps1",
    "Invoke-OrchestratorAgentAction.ps1",
    "Restart-OrchMcpServer.ps1",
    "Start-OrchestratorServices.ps1",
    "Test-OrchTunnelCanary.ps1",
    "Start-ActiveAgentFleet.ps1"
)) {
    if ($content -notmatch [regex]::Escape($helper)) {
        throw "MCP server does not delegate to expected helper: $helper"
    }
}

foreach ($exactTaskSelectorToken in @("task_path", "task_name", "-TaskPath", "-TaskName")) {
    if ($content -notmatch [regex]::Escape($exactTaskSelectorToken)) {
        throw "MCP agent start contract is missing exact task selector token: $exactTaskSelectorToken"
    }
}

if ($content -notmatch "Get-McpCapabilityStatusTool") {
    throw "MCP server must expose the connector capability status helper through a dedicated tool function."
}

if ($content -notmatch "Invoke-JsonScript") {
    throw "MCP server must parse JSON helper output through Invoke-JsonScript."
}

if ($serverContent -notmatch [regex]::Escape("Start-OrchMcpServer.Tools.ps1")) {
    throw "MCP server must dot-source Start-OrchMcpServer.Tools.ps1."
}

if ($serverContent -notmatch "Bearer") {
    throw "MCP server must keep bearer-token authorization support."
}

if ($serverContent -notmatch "Write-SseResponse") {
    throw "MCP server must expose an SSE-compatible response writer for ChatGPT connector transport."
}

if ($serverContent -notmatch "text/event-stream") {
    throw "MCP server must support text/event-stream responses."
}

if ($serverContent -notmatch "New-McpInitializeResult") {
    throw "MCP initialize response must be centralized for JSON and streaming transports."
}

if ($serverContent -notmatch "Handle-McpJsonRpcRequest") {
    throw "MCP JSON-RPC request handling must be transport-independent."
}

if ($serverContent -notmatch 'protocolVersion = "2025-03-26"') {
    throw "MCP initialize response must advertise the expected protocol version."
}

Write-Host "Validated MCP server control and ChatGPT connector compatibility contract."
