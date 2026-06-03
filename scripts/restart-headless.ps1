#!/usr/bin/env pwsh
# Lantern OS Headless Restart Script (Windows)
# Usage: .\scripts\restart-headless.ps1
# Restarts all Lantern OS services in Docker containers.
# No dashboards. No GUIs. Just headless APIs.

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Write-Host "=== Lantern OS Headless Restart ===" -ForegroundColor Cyan

# 1. Check Docker
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error "Docker not found. Install Docker Desktop first."
    exit 1
}

docker compose --version | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Error "docker compose not available."
    exit 1
}

# 2. Ensure data directories exist
$dirs = @(
    "$ProjectRoot\data\archives",
    "$ProjectRoot\data\logs",
    "$ProjectRoot\assets\brand",
    "$ProjectRoot\assets\incoming"
)
foreach ($d in $dirs) {
    if (-not (Test-Path $d)) {
        New-Item -ItemType Directory -Path $d -Force | Out-Null
        Write-Host "Created: $d"
    }
}

# 3. Pull/build images and restart
Write-Host "`nBuilding and starting services..." -ForegroundColor Yellow
Set-Location $ProjectRoot
$prevPreference = $ErrorActionPreference
$ErrorActionPreference = "Continue"
docker compose -f docker-compose.headless.yml down --remove-orphans 2>$null
$downExit = $LASTEXITCODE
docker compose -f docker-compose.headless.yml up -d --build
$upExit = $LASTEXITCODE
$ErrorActionPreference = $prevPreference

if ($upExit -ne 0) {
    Write-Error "Docker compose failed. Check logs: docker compose -f docker-compose.headless.yml logs"
    exit 1
}

# 4. Health check
Write-Host "`nHealth checks..." -ForegroundColor Yellow
$services = @("lantern-csf", "lantern-cadd", "lantern-proxy")
$maxWait = 30
$waited = 0
while ($waited -lt $maxWait) {
    $allHealthy = $true
    foreach ($svc in $services) {
        $status = docker inspect --format='{{.State.Status}}' $svc 2>$null
        if ($status -ne "running") {
            $allHealthy = $false
        }
    }
    if ($allHealthy) { break }
    Start-Sleep -Seconds 1
    $waited++
}

# 5. Report
Write-Host "`n=== Status ===" -ForegroundColor Green
docker compose -f docker-compose.headless.yml ps

Write-Host "`n=== Endpoints ===" -ForegroundColor Green
Write-Host "  Health: http://localhost/health"
Write-Host "  CSF:    http://localhost/csf/"

Write-Host "`n=== Logs ===" -ForegroundColor Green
Write-Host "  docker compose -f docker-compose.headless.yml logs -f"
Write-Host "`nRestart complete. No dashboards. No GUIs. Just APIs." -ForegroundColor Cyan
