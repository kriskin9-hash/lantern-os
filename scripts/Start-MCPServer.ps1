#Requires -Version 7
<#
.SYNOPSIS
    Start the Lantern OS MCP Server.
.DESCRIPTION
    Launches the FastAPI MCP server on port 8770 (default).
    Set MCP_SERVER_PORT env var to override.
#>

param(
    [int]$Port = 8771,
    [string]$Host = "127.0.0.1",
    [switch]$Background
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot | Resolve-Path

Write-Host "[MCP] Starting Lantern OS MCP Server..." -ForegroundColor Cyan
Write-Host "[MCP] Repo: $repoRoot" -ForegroundColor Gray
Write-Host "[MCP] Endpoint: http://${Host}:${Port}" -ForegroundColor Gray

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
$env:MCP_SERVER_HOST = $Host

# Start server
$serverScript = Join-Path $serverDir "server.py"
if (-not (Test-Path $serverScript)) {
    Write-Error "MCP server script not found: $serverScript"
}

if ($Background) {
    $proc = Start-Process python -ArgumentList $serverScript -WorkingDirectory $repoRoot -WindowStyle Hidden -PassThru
    Write-Host "[MCP] Server started in background (PID: $($proc.Id))" -ForegroundColor Green
    Write-Host "[MCP] Health: http://${Host}:${Port}/health" -ForegroundColor Green
    return $proc.Id
} else {
    Write-Host "[MCP] Starting in foreground..." -ForegroundColor Green
    & python $serverScript
}
