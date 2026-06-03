#!/usr/bin/env pwsh
# Lantern OS Headless Status Checker
# Usage: .\scripts\status.ps1

$ErrorActionPreference = "Stop"

Write-Host "=== Lantern OS Headless Status ===" -ForegroundColor Cyan

# Check Docker
$dockerRunning = $false
try {
    docker info | Out-Null
    $dockerRunning = $true
} catch {}

if (-not $dockerRunning) {
    Write-Host "Docker: NOT RUNNING" -ForegroundColor Red
    Write-Host "  Fix: Start Docker Desktop or Docker service"
    exit 1
} else {
    Write-Host "Docker: RUNNING" -ForegroundColor Green
}

# Container status
$containers = @("lantern-csf", "lantern-cadd", "lantern-proxy")
Write-Host "`nContainers:" -ForegroundColor Yellow
foreach ($c in $containers) {
    $status = docker inspect --format='{{.State.Status}}' $c 2>$null
    $health = docker inspect --format='{{.State.Health.Status}}' $c 2>$null
    if ($LASTEXITCODE -eq 0 -and $status) {
        $color = if ($status -eq "running") { "Green" } else { "Red" }
        $healthStr = if ($health) { " (health: $health)" } else { "" }
        Write-Host "  $c`: $status$healthStr" -ForegroundColor $color
    } else {
        Write-Host "  $c`: not found" -ForegroundColor Red
    }
}

# Port checks
Write-Host "`nPorts:" -ForegroundColor Yellow
$ports = @(
    @(80, "proxy"),
    @(9000, "csf-worker")
)
foreach ($p in $ports) {
    $port = $p[0]
    $name = $p[1]
    $listener = $null
    try {
        $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $port)
        $listener.Start()
        $listener.Stop()
        Write-Host "  Port $port ($name): available" -ForegroundColor Gray
    } catch {
        Write-Host "  Port $port ($name): IN USE (service running)" -ForegroundColor Green
    }
}

# Volume checks
Write-Host "`nVolumes:" -ForegroundColor Yellow
$vols = @(
    @("./data/archives", "Archive storage"),
    @("./data/logs", "Log files"),
    @("./assets/brand", "Brand assets"),
    @("./assets/incoming", "Incoming assets")
)
foreach ($v in $vols) {
    $path = $v[0]
    $desc = $v[1]
    if (Test-Path $path) {
        $size = (Get-ChildItem $path -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
        $sizeStr = if ($size -gt 1GB) { "{0:N2} GB" -f ($size / 1GB) } elseif ($size -gt 1MB) { "{0:N2} MB" -f ($size / 1MB) } else { "{0:N0} bytes" -f $size }
        Write-Host "  $path`: OK ($sizeStr) — $desc" -ForegroundColor Green
    } else {
        Write-Host "  $path`: MISSING — $desc" -ForegroundColor Red
    }
}

# Endpoint checks
Write-Host "`nEndpoints:" -ForegroundColor Yellow
$endpoints = @(
    @("http://localhost/health", "proxy health"),
    @("http://localhost/csf/health", "csf health")
)
foreach ($ep in $endpoints) {
    $url = $ep[0]
    $name = $ep[1]
    try {
        $resp = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        Write-Host "  $name`: OK ($($resp.StatusCode))" -ForegroundColor Green
    } catch {
        Write-Host "  $name`: UNREACHABLE" -ForegroundColor Red
    }
}

Write-Host "`n=== Quick Actions ===" -ForegroundColor Cyan
Write-Host "  Restart: .\scripts\restart-headless.ps1"
Write-Host "  Logs:    docker compose -f docker-compose.headless.yml logs -f"
Write-Host "  Stop:    docker compose -f docker-compose.headless.yml down"
