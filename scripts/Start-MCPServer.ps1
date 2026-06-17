#Requires -Version 7
<#
.SYNOPSIS
    Start the Lantern OS MCP Server.
.DESCRIPTION
    Launches the FastAPI MCP server on port 8771 by default.

    The default launcher is src/mcp_server/server_modern.py. It preserves the
    legacy /sse + /messages MCP transport and adds the modern connector surface:

      GET  /status
      GET  /capabilities
      GET  /tools
      GET  /receipts
      GET  /mcp
      POST /mcp
      GET  /mcp/sse

    Set MCP_SERVER_PORT or pass -Port to override.
#>

param(
    [int]$Port = 8771,
    [string]$BindHost = "127.0.0.1",
    [switch]$Background,
    [switch]$Legacy
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot | Resolve-Path

Write-Host "[MCP] Starting Lantern OS MCP Server..." -ForegroundColor Cyan
Write-Host "[MCP] Repo: $repoRoot" -ForegroundColor Gray
Write-Host "[MCP] Endpoint: http://${BindHost}:${Port}" -ForegroundColor Gray
Write-Host "[MCP] Modern:  http://${BindHost}:${Port}/mcp" -ForegroundColor Gray
Write-Host "[MCP] Legacy:  http://${BindHost}:${Port}/sse + /messages" -ForegroundColor Gray

# Check Python
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Error "Python not found. Install Python 3.10+ and try again."
}

# Install deps if needed
$serverDir = Join-Path $repoRoot "src\mcp_server"
$reqFile = Join-Path $serverDir "requirements.txt"
if (Test-Path $reqFile) {
    Write-Host "[MCP] Checking dependencies..." -ForegroundColor Gray
    & python -m pip install -q -r $reqFile
}

# Set env
$env:MCP_SERVER_PORT = $Port
$env:MCP_SERVER_HOST = $BindHost

# Start server. server_modern.py wraps server.py and keeps old routes alive.
$serverScriptName = if ($Legacy) { "server.py" } else { "server_modern.py" }
$serverScript = Join-Path $serverDir $serverScriptName
if (-not (Test-Path $serverScript)) {
    Write-Error "MCP server script not found: $serverScript"
}

if ($Background) {
    $proc = Start-Process python -ArgumentList $serverScript -WorkingDirectory $repoRoot -WindowStyle Hidden -PassThru
    Write-Host "[MCP] Server started in background (PID: $($proc.Id))" -ForegroundColor Green
    Write-Host "[MCP] Health:       http://${BindHost}:${Port}/health" -ForegroundColor Green
    Write-Host "[MCP] Status:       http://${BindHost}:${Port}/status" -ForegroundColor Green
    Write-Host "[MCP] Capabilities: http://${BindHost}:${Port}/capabilities" -ForegroundColor Green
    Write-Host "[MCP] Tools:        http://${BindHost}:${Port}/tools" -ForegroundColor Green
    Write-Host "[MCP] MCP:          http://${BindHost}:${Port}/mcp" -ForegroundColor Green
    return $proc.Id
} else {
    Write-Host "[MCP] Starting in foreground..." -ForegroundColor Green
    & python $serverScript
}
