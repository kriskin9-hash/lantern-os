#Requires -Version 5.0
<#
.SYNOPSIS
    Aggressive dev launcher with hot reload for all Lantern OS services.
.DESCRIPTION
    1. Kills ALL existing Lantern-related processes (node, python) — no orphans.
    2. Auto-detects .env.local and warns if no provider keys.
    3. Starts Lantern Garage with node --watch (hot reload).
    4. Optionally starts MCP server and Discord bot.
    5. Opens browser automatically.
    Run from repo root or pass -LanternRoot.
.PARAMETER LanternRoot
    Path to lantern-os repo. Defaults to current directory.
.PARAMETER MCP
    Also start MCP server on port 8771.
.PARAMETER Discord
    Also start Discord bot.
.PARAMETER NoBrowser
    Don't auto-open browser.
.EXAMPLE
    .\scripts\Start-LanternDev.ps1
.EXAMPLE
    .\scripts\Start-LanternDev.ps1 -MCP -Discord
#>
param(
    [string]$LanternRoot = (Get-Location).Path,
    [switch]$MCP,
    [switch]$Discord,
    [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"

function Write-Step($msg) { Write-Host "  → $msg" -ForegroundColor Cyan }
function Write-OK($msg)   { Write-Host "  ✓ $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "  ⚠ $msg" -ForegroundColor Yellow }
function Write-Err($msg)  { Write-Host "  ✗ $msg" -ForegroundColor Red }

Write-Host ""
Write-Host "  Lantern OS — Dev Mode (Hot Reload)" -ForegroundColor Yellow
Write-Host "  ─────────────────────────────────" -ForegroundColor DarkGray
Write-Host ""

# ── Pre-flight checks ──────────────────────────────────────────────────────

try {
    $nodeVer = node --version 2>&1
    Write-OK "Node.js $nodeVer"
} catch {
    Write-Err "Node.js not found. Install from https://nodejs.org"
    exit 1
}

try {
    $pyVer = python --version 2>&1
    Write-OK "$pyVer"
} catch {
    Write-Warn "Python not found — MCP/Discord skipped if requested"
}

$serverPath = Join-Path $LanternRoot "apps\lantern-garage\server.js"
if (-not (Test-Path $serverPath)) {
    Write-Err "server.js not found at $serverPath"
    Write-Warn "Is -LanternRoot correct? Current: $LanternRoot"
    exit 1
}

# Install npm deps if missing
$nodeModules = Join-Path $LanternRoot "apps\lantern-garage\node_modules"
if (-not (Test-Path $nodeModules)) {
    Write-Step "Installing npm dependencies..."
    Push-Location (Join-Path $LanternRoot "apps\lantern-garage")
    npm install --silent
    Pop-Location
    Write-OK "Dependencies installed."
}

# ── AGGRESSIVE KILL: all Lantern-related processes ─────────────────────────

Write-Step "Terminating any existing Lantern OS processes..."

# Kill node processes running server.js or lantern-garage
$nodeProcs = Get-Process -Name "node" -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*server.js*" -or
    $_.CommandLine -like "*lantern-garage*" -or
    $_.CommandLine -like "*cloud-server.js*"
}
if ($nodeProcs) {
    $nodeProcs | Stop-Process -Force
    Write-OK "Stopped $($nodeProcs.Count) node process(es)"
} else {
    Write-OK "No lingering node processes"
}

# Kill python processes running MCP or Discord bot
$pyProcs = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*mcp_server*" -or
    $_.CommandLine -like "*discord_lounge_bot*"
}
if ($pyProcs) {
    $pyProcs | Stop-Process -Force
    Write-OK "Stopped $($pyProcs.Count) python process(es)"
} else {
    Write-OK "No lingering python processes"
}

# Brief pause for port release
Start-Sleep -Milliseconds 800

# ── Check .env.local ───────────────────────────────────────────────────────

$envLocal = Join-Path $LanternRoot "apps\lantern-garage\.env.local"
if (Test-Path $envLocal) {
    $hasKey = Select-String -Path $envLocal -Pattern "^(ANTHROPIC|OPENAI|GEMINI|GOOGLE|XAI)_API_KEY=" -Quiet
    if (-not $hasKey) {
        Write-Warn ".env.local exists but no provider API keys found."
        Write-Warn "  Add at least one key: GEMINI_API_KEY, ANTHROPIC_API_KEY, etc."
    } else {
        Write-OK ".env.local has provider keys"
    }
} else {
    Write-Warn ".env.local not found. Create one:"
    Write-Warn "  echo 'GEMINI_API_KEY=your_key' > apps\lantern-garage\.env.local"
}

# ── Start Lantern Garage with HOT RELOAD ─────────────────────────────────

Write-Step "Starting Lantern Garage (hot reload) on port 4177..."

$garageDir = Join-Path $LanternRoot "apps\lantern-garage"

# Use node --watch for hot reload; window visible so you can see restarts
$garageProc = Start-Process `
    -FilePath "node" `
    -ArgumentList "--watch", "server.js" `
    -WorkingDirectory $garageDir `
    -PassThru `
    -WindowStyle Normal

Start-Sleep -Seconds 3

# Health check
$healthOk = $false
for ($i = 0; $i -lt 5; $i++) {
    try {
        $health = Invoke-RestMethod -Uri "http://127.0.0.1:4177/api/status" -TimeoutSec 3 -ErrorAction Stop
        Write-OK "Lantern Garage running (PID $($garageProc.Id)) — hot reload active"
        Write-Host "    http://127.0.0.1:4177" -ForegroundColor White
        $healthOk = $true
        break
    } catch {
        Start-Sleep -Seconds 1
    }
}
if (-not $healthOk) {
    Write-Err "Server failed to start. Check the node window for errors."
    exit 1
}

# ── Start MCP (optional) ─────────────────────────────────────────────────

if ($MCP) {
    Write-Host ""
    Write-Step "Starting MCP server on port 8771..."

    $mcpScript = Join-Path $LanternRoot "src\mcp_server\server.py"
    if (-not (Test-Path $mcpScript)) {
        Write-Warn "MCP script not found — skipped"
    } else {
        $mcpProc = Start-Process `
            -FilePath "python" `
            -ArgumentList $mcpScript `
            -WorkingDirectory $LanternRoot `
            -PassThru `
            -WindowStyle Normal

        Start-Sleep -Seconds 3
        try {
            $mcpHealth = Invoke-RestMethod -Uri "http://127.0.0.1:8771/health" -TimeoutSec 5 -ErrorAction Stop
            Write-OK "MCP server running (PID $($mcpProc.Id)) — $($mcpHealth.slots_online) slots online"
        } catch {
            Write-Warn "MCP started but health check failed"
        }
    }
}

# ── Start Discord Bot (optional) ─────────────────────────────────────────

if ($Discord) {
    Write-Host ""
    Write-Step "Starting Discord bot..."

    $botScript = Join-Path $LanternRoot "src\discord_lounge_bot\bot.py"
    if (-not (Test-Path $botScript)) {
        Write-Warn "Discord bot script not found — skipped"
    } else {
        $botProc = Start-Process `
            -FilePath "python" `
            -ArgumentList $botScript `
            -WorkingDirectory $LanternRoot `
            -PassThru `
            -WindowStyle Normal
        Write-OK "Discord bot started (PID $($botProc.Id))"
    }
}

# ── Open browser ──────────────────────────────────────────────────────────

if (-not $NoBrowser) {
    Start-Sleep -Seconds 1
    Start-Process "http://127.0.0.1:4177"
}

# ── Summary ──────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "  ─────────────────────────────────" -ForegroundColor DarkGray
Write-OK "Lantern OS dev stack running."
Write-Host ""
Write-Host "  Web:     http://127.0.0.1:4177  (hot reload)" -ForegroundColor White
if ($MCP) { Write-Host "  MCP:     http://127.0.0.1:8771" -ForegroundColor White }
if ($Discord) { Write-Host "  Discord: bot active" -ForegroundColor White }
Write-Host ""
Write-Host "  Edit any file in apps/lantern-garage/routes/ or lib/" -ForegroundColor Gray
Write-Host "  Node --watch will auto-restart the server." -ForegroundColor Gray
Write-Host ""
