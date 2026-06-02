#Requires -Version 5.0
<#
.SYNOPSIS
    Start all Lantern OS services.
.DESCRIPTION
    Starts Lantern Garage (Dream Journal) on port 4177.
    Optionally starts MCP server on port 8771.
    Run with -RegisterAutostart to create a Windows Task Scheduler entry.
.PARAMETER LanternRoot
    Path to lantern-os repo. Defaults to current directory.
.PARAMETER MCP
    Also start the MCP server on port 8771.
.PARAMETER RegisterAutostart
    Register Lantern Garage as a Windows login autostart task (requires Admin).
.PARAMETER UnregisterAutostart
    Remove the autostart task.
.EXAMPLE
    .\scripts\Start-Lantern.ps1
.EXAMPLE
    .\scripts\Start-Lantern.ps1 -MCP
.EXAMPLE
    .\scripts\Start-Lantern.ps1 -RegisterAutostart
#>
param(
    [string]$LanternRoot = (Get-Location).Path,
    [switch]$MCP,
    [switch]$RegisterAutostart,
    [switch]$UnregisterAutostart
)

$ErrorActionPreference = "Stop"
$TaskName = "LanternDreamJournal"

function Write-Step($msg) { Write-Host "  $msg" -ForegroundColor Cyan }
function Write-OK($msg)   { Write-Host "  ✓ $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "  ⚠ $msg" -ForegroundColor Yellow }
function Write-Err($msg)  { Write-Host "  ✗ $msg" -ForegroundColor Red }

# ── Autostart registration ─────────────────────────────────────────────────

if ($UnregisterAutostart) {
    if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-OK "Autostart task '$TaskName' removed."
    } else {
        Write-Warn "No autostart task named '$TaskName' found."
    }
    exit 0
}

if ($RegisterAutostart) {
    $nodeExe = (Get-Command node -ErrorAction Stop).Source
    $serverScript = Join-Path $LanternRoot "apps\lantern-garage\server.js"

    $action = New-ScheduledTaskAction `
        -Execute $nodeExe `
        -Argument "`"$serverScript`"" `
        -WorkingDirectory $LanternRoot

    $trigger = New-ScheduledTaskTrigger -AtLogon

    $settings = New-ScheduledTaskSettingsSet `
        -ExecutionTimeLimit (New-TimeSpan -Hours 0) `
        -RestartCount 3 `
        -RestartInterval (New-TimeSpan -Minutes 1)

    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -RunLevel Highest `
        -Force | Out-Null

    Write-OK "Autostart registered: '$TaskName'"
    Write-Host "    Lantern Garage will start at next login." -ForegroundColor Gray
    Write-Host "    To remove: .\scripts\Start-Lantern.ps1 -UnregisterAutostart" -ForegroundColor Gray
    exit 0
}

# ── Pre-flight ─────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "  Lantern OS — Dream Journal" -ForegroundColor Yellow
Write-Host "  ──────────────────────────" -ForegroundColor DarkGray
Write-Host ""

# Check Node.js
try {
    $nodeVer = node --version 2>&1
    Write-OK "Node.js $nodeVer"
} catch {
    Write-Err "Node.js not found. Install from https://nodejs.org"
    exit 1
}

# Check repo
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

# ── Kill existing instances ────────────────────────────────────────────────

$existing = Get-Process -Name "node" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -like "*lantern-garage*" }
if ($existing) {
    Write-Step "Stopping existing Lantern Garage instance..."
    $existing | Stop-Process -Force
    Start-Sleep -Milliseconds 500
    Write-OK "Stopped."
}

# ── Start Lantern Garage ───────────────────────────────────────────────────

Write-Step "Starting Lantern Garage on port 4177..."

$garageDir = Join-Path $LanternRoot "apps\lantern-garage"
$logPath   = Join-Path $LanternRoot "logs\lantern-garage.log"
New-Item -ItemType Directory -Path (Split-Path $logPath) -Force | Out-Null

$proc = Start-Process `
    -FilePath "node" `
    -ArgumentList "server.js" `
    -WorkingDirectory $garageDir `
    -RedirectStandardOutput $logPath `
    -RedirectStandardError "$logPath.err" `
    -PassThru `
    -WindowStyle Hidden

Start-Sleep -Seconds 2

# Health check
try {
    $health = Invoke-RestMethod -Uri "http://127.0.0.1:4177/" -TimeoutSec 5 -ErrorAction Stop
    Write-OK "Lantern Garage running (PID $($proc.Id))"
    Write-Host "    http://127.0.0.1:4177" -ForegroundColor White
} catch {
    Write-Warn "Server started but health check failed. Check: $logPath"
}

# ── Start MCP (optional) ───────────────────────────────────────────────────

if ($MCP) {
    Write-Host ""
    Write-Step "Starting MCP server on port 8771..."

    $venvPython = Join-Path $LanternRoot ".venv\Scripts\python.exe"
    $mcpScript  = Join-Path $LanternRoot "src\mcp_server\server.py"

    if (-not (Test-Path $venvPython)) {
        Write-Warn ".venv not found at $LanternRoot\.venv — MCP skipped."
        Write-Warn "Create it: python -m venv .venv && .venv\Scripts\pip install -e ."
    } elseif (-not (Test-Path $mcpScript)) {
        Write-Warn "MCP server script not found at $mcpScript — skipped."
    } else {
        $mcpLog = Join-Path $LanternRoot "logs\mcp-server.log"
        Start-Process `
            -FilePath $venvPython `
            -ArgumentList $mcpScript `
            -WorkingDirectory $LanternRoot `
            -RedirectStandardOutput $mcpLog `
            -RedirectStandardError "$mcpLog.err" `
            -WindowStyle Hidden | Out-Null

        Start-Sleep -Seconds 2
        try {
            $mcpHealth = Invoke-RestMethod -Uri "http://127.0.0.1:8771/health" -TimeoutSec 5 -ErrorAction Stop
            Write-OK "MCP server running — $($mcpHealth.slots_online) slots online"
            Write-Host "    http://127.0.0.1:8771" -ForegroundColor White
        } catch {
            Write-Warn "MCP started but health check failed. Check: $mcpLog"
        }
    }
}

# ── Summary ────────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "  ──────────────────────────" -ForegroundColor DarkGray
Write-OK "Lantern is running."
Write-Host ""
Write-Host "  Open in browser: http://127.0.0.1:4177" -ForegroundColor White
Write-Host "  To autostart at login: .\scripts\Start-Lantern.ps1 -RegisterAutostart" -ForegroundColor Gray
Write-Host "  Logs: $logPath" -ForegroundColor Gray
Write-Host ""
