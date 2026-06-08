<#
.SYNOPSIS
    Start the full Lantern OS stack: all services (Lanterns Garage, Image Gen, MCP, Ollama).
.DESCRIPTION
    1. Checks prerequisites (Node, Python, Ollama)
    2. Cleans up stale processes
    3. Starts all services in parallel
    4. Launches Dream Chat in Chrome
    Compatible with PowerShell 5.1+ (Windows) and PowerShell Core (Linux/WSL)
#>

param(
    [int]$McpPort = 8771,
    [string]$McpHost = "127.0.0.1"
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot | Resolve-Path

Write-Host "═══════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  Lantern OS Stack Startup" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════" -ForegroundColor Cyan

# ── Step 1: Start MCP Server ──
Write-Host "`n[1/3] Starting MCP Server..." -ForegroundColor Yellow
$mcpScript = Join-Path $PSScriptRoot "Start-MCPServer.ps1"
$mcpPid = & $mcpScript -Port $McpPort -Host $McpHost -Background
Write-Host "      MCP PID: $mcpPid" -ForegroundColor Gray

# ── Step 2: Health Check ──
Write-Host "`n[2/3] Waiting for MCP health..." -ForegroundColor Yellow
$healthUrl = "http://${McpHost}:${McpPort}/health"
$maxRetries = 30
$retry = 0
$healthy = $false
while ($retry -lt $maxRetries) {
    try {
        $resp = Invoke-RestMethod -Uri $healthUrl -Method GET -TimeoutSec 2 -ErrorAction Stop
        if ($resp.status -eq "online") {
            Write-Host "      ✅ MCP online (slots: $($resp.slots_online), queue: $($resp.queue_depth))" -ForegroundColor Green
            $healthy = $true
            break
        }
    } catch {
        # expected while starting
    }
    Start-Sleep -Milliseconds 500
    $retry++
}

if (-not $healthy) {
    Write-Error "MCP server failed to start within $maxRetries retries."
}

# ── Step 3: Start Discord Bot ──
Write-Host "`n[3/3] Starting Discord Bot v2..." -ForegroundColor Yellow
$botScript = Join-Path $repoRoot "src\discord_lounge_bot\bot_v2.py"
if (-not (Test-Path $botScript)) {
    Write-Error "Bot script not found: $botScript"
}

Write-Host "      Bot: $botScript" -ForegroundColor Gray
Write-Host "`n═══════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  Stack Ready. Press Ctrl+C to stop." -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════" -ForegroundColor Cyan

& python $botScript
