#Requires -Version 5.1
<#
.SYNOPSIS
    Start the Dream Journal (Node.js) server for Lantern OS.

.DESCRIPTION
    Launches the Lantern Garage Node.js server on 127.0.0.1:4177.
    If the server is already running, opens the browser instead.
    Discord bot starts automatically when DISCORD_BOT_TOKEN and
    LANTERN_DISCORD_GUILD_ID are set in .env.

.PARAMETER Port
    Override the default port (4177).

.EXAMPLE
    .\scripts\Start-DreamJournal.ps1

.EXAMPLE
    .\scripts\Start-DreamJournal.ps1 -Port 5177
#>
param(
    [int]$Port = 4177
)

$ErrorActionPreference = "Stop"

$root      = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$serverJs  = Join-Path $root "apps\lantern-garage\server.js"
$appUrl    = "http://127.0.0.1:$Port"
$healthUrl = "$appUrl/api/health"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
function Test-ServerHealth {
    try {
        $r = Invoke-WebRequest -Uri $healthUrl -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        return ($r.StatusCode -eq 200)
    } catch {
        return $false
    }
}

# Already running?
if (Test-ServerHealth) {
    Write-Host "Dream Journal is already running at $appUrl" -ForegroundColor Green
    Start-Process $appUrl
    return
}

# Validate node.js
if (-not (Get-Command "node" -ErrorAction SilentlyContinue)) {
    Write-Error "node.exe not found.`nInstall Node.js 18+ from https://nodejs.org and re-run."
    exit 1
}

# Validate server.js exists
if (-not (Test-Path $serverJs)) {
    Write-Error "Server not found at $serverJs`nRe-run the installer or clone the repo first."
    exit 1
}

# Validate npm deps
$pkgLock = Join-Path $root "apps\lantern-garage\node_modules"
if (-not (Test-Path $pkgLock)) {
    Write-Host "  [!] node_modules missing — running npm install first..." -ForegroundColor Yellow
    Push-Location (Join-Path $root "apps\lantern-garage")
    npm install --loglevel=error
    Pop-Location
}

# Copy .env.example → .env if no .env exists
$envFile    = Join-Path $root ".env"
$envExample = Join-Path $root ".env.example"
if (-not (Test-Path $envFile) -and (Test-Path $envExample)) {
    Copy-Item $envExample $envFile
    Write-Host "  [+] Created .env from .env.example" -ForegroundColor Cyan
    Write-Host "      Edit $envFile and add your API keys." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "  Lantern OS / Dream Journal" -ForegroundColor Cyan
Write-Host "  URL  : $appUrl" -ForegroundColor White
Write-Host "  Root : $root" -ForegroundColor Gray
Write-Host ""

Set-Location -LiteralPath $root
$env:LANTERN_GARAGE_PORT = "$Port"
node $serverJs
