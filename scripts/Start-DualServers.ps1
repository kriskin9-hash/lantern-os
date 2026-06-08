<#
.SYNOPSIS
    Lantern OS Dual-Boot Quickstart
    Starts two servers simultaneously: stable release (port 4177) + dev branch (port 4178)
    
.DESCRIPTION
    This script implements the documented dual-boot system from QUICKSTART.md:
    - Port 4177: Stable release (master branch, checked out fresh)
    - Port 4178: Development (current working branch, with hot-reload)
    
    Both run concurrently. Open http://127.0.0.1:4177 for stable, :4178 for dev.
    
.PARAMETER NoChrome
    Skip auto-launching Chrome
    
.EXAMPLE
    pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/Start-DualServers.ps1
    pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/Start-DualServers.ps1 -NoChrome
#>

param(
    [switch]$NoChrome
)

$ErrorActionPreference = "Continue"
$RepoRoot = Split-Path -Parent $PSScriptRoot | Resolve-Path
$AppRoot = Join-Path $RepoRoot "apps" "lantern-garage"

Write-Host ""
Write-Host "🚀 Lantern OS — Dual Boot Quickstart" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""

# Verify prerequisites
Write-Host "📋 Checking prerequisites..." -ForegroundColor Yellow
$hasNode = $null -ne (Get-Command node -ErrorAction SilentlyContinue)
$hasGit = $null -ne (Get-Command git -ErrorAction SilentlyContinue)

if (-not $hasNode -or -not $hasGit) {
    Write-Host "❌ Missing: Node.js or Git" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Node.js $(node --version)" -ForegroundColor Green
Write-Host "✓ Git (installed)" -ForegroundColor Green
Write-Host ""

# Install dependencies
Write-Host "📦 Installing dependencies..." -ForegroundColor Yellow
Push-Location $AppRoot
npm install --silent 2>&1 | Out-Null
Pop-Location
Write-Host "✓ Dependencies ready" -ForegroundColor Green
Write-Host ""

# Helper: Get current branch
function Get-CurrentBranch {
    git rev-parse --abbrev-ref HEAD 2>$null
}

# Helper: Kill process on port
function Stop-ProcessOnPort {
    param([int]$Port)
    try {
        $proc = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue | 
            Select-Object -ExpandProperty OwningProcess | Get-Unique
        if ($proc) {
            Stop-Process -Id $proc -Force -ErrorAction SilentlyContinue
            Start-Sleep -Milliseconds 500
        }
    }
    catch { }
}

# Clean up old processes
Write-Host "🧹 Cleaning up stale processes..." -ForegroundColor Yellow
Stop-ProcessOnPort -Port 4177
Stop-ProcessOnPort -Port 4178
Write-Host "✓ Ports cleared" -ForegroundColor Green
Write-Host ""

# Get current branch (for dev server)
$devBranch = Get-CurrentBranch
Write-Host "🌳 Current branch: $devBranch" -ForegroundColor Cyan

# Start Stable Server (Master on Port 4177)
Write-Host ""
Write-Host "🔵 Server 1: Stable Release (port 4177)" -ForegroundColor Blue
Write-Host "  → Checking out master..." -ForegroundColor Gray

Push-Location $RepoRoot
git fetch origin --quiet
git checkout master --quiet 2>&1 | Out-Null
git pull origin master --quiet 2>&1 | Out-Null
Pop-Location

Push-Location $AppRoot
Write-Host "  → Starting on port 4177..." -ForegroundColor Gray
$stableProc = Start-Process -FilePath "node" `
    -ArgumentList "server.js" `
    -EnvironmentVariable @{"PORT"="4177"} `
    -WindowStyle Hidden `
    -PassThru `
    -ErrorAction SilentlyContinue
Pop-Location

if ($stableProc) {
    Write-Host "  ✓ Running (PID $($stableProc.Id))" -ForegroundColor Green
} else {
    Write-Host "  ❌ Failed to start" -ForegroundColor Red
    exit 1
}

Start-Sleep -Seconds 2

# Start Dev Server (Current Branch on Port 4178)
Write-Host ""
Write-Host "🟢 Server 2: Development ($devBranch on port 4178)" -ForegroundColor Green
Write-Host "  → Starting with hot-reload..." -ForegroundColor Gray

Push-Location $AppRoot
$devProc = Start-Process -FilePath "node" `
    -ArgumentList "--watch", "server.js" `
    -EnvironmentVariable @{"PORT"="4178"} `
    -WindowStyle Hidden `
    -PassThru `
    -ErrorAction SilentlyContinue
Pop-Location

if ($devProc) {
    Write-Host "  ✓ Running (PID $($devProc.Id))" -ForegroundColor Green
} else {
    Write-Host "  ❌ Failed to start" -ForegroundColor Red
    exit 1
}

Start-Sleep -Seconds 2

# Health check
Write-Host ""
Write-Host "💊 Health check..." -ForegroundColor Yellow
$stable = $null
$dev = $null

1..5 | ForEach-Object {
    try {
        $resp = Invoke-WebRequest -Uri "http://127.0.0.1:4177/api/version" -ErrorAction SilentlyContinue -SkipHttpErrorCheck -TimeoutSec 2
        if ($resp.StatusCode -eq 200) { $stable = $true }
    } catch { }
    
    try {
        $resp = Invoke-WebRequest -Uri "http://127.0.0.1:4178/api/version" -ErrorAction SilentlyContinue -SkipHttpErrorCheck -TimeoutSec 2
        if ($resp.StatusCode -eq 200) { $dev = $true }
    } catch { }
    
    if ($stable -and $dev) { break }
    Start-Sleep -Milliseconds 500
}

if ($stable) { Write-Host "  ✓ Stable (4177) responding" -ForegroundColor Green }
else { Write-Host "  ⚠ Stable (4177) still initializing..." -ForegroundColor Yellow }

if ($dev) { Write-Host "  ✓ Dev (4178) responding" -ForegroundColor Green }
else { Write-Host "  ⚠ Dev (4178) still initializing..." -ForegroundColor Yellow }

# Launch browser
Write-Host ""
if (-not $NoChrome) {
    Write-Host "🌐 Opening Chrome..." -ForegroundColor Yellow
    try {
        Start-Process "chrome.exe" "http://127.0.0.1:4177/dream-chat.html" -ErrorAction SilentlyContinue
        Write-Host "  ✓ Opened stable (4177)" -ForegroundColor Green
    }
    catch {
        Write-Host "  ⚠ Chrome not found" -ForegroundColor Yellow
    }
}

# Summary
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "✅ Dual Boot Running!" -ForegroundColor Green
Write-Host ""
Write-Host "🔵 Stable: http://127.0.0.1:4177" -ForegroundColor Blue
Write-Host "🟢 Dev:    http://127.0.0.1:4178" -ForegroundColor Green
Write-Host ""
Write-Host "📚 Read QUICKSTART.md and AGENTS.md before next session" -ForegroundColor Cyan
Write-Host ""

while ($true) { Start-Sleep -Seconds 10 }
