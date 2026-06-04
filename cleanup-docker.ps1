#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Docker cleanup and resource optimization script for Lantern OS Dream Journal
.DESCRIPTION
    Removes unused images, containers, volumes, and build cache to reclaim disk space
    and reduce Docker resource footprint.
#>

Write-Host "🧹 Lantern OS Docker Cleanup" -ForegroundColor Cyan

# Stop all running containers
Write-Host "`n[1/4] Stopping containers..." -ForegroundColor Yellow
$running = docker ps -q
if ($running) {
    docker stop $running
    Write-Host "✓ Containers stopped" -ForegroundColor Green
} else {
    Write-Host "✓ No running containers" -ForegroundColor Green
}

# Remove exited containers
Write-Host "`n[2/4] Removing exited containers..." -ForegroundColor Yellow
docker container prune -f --filter "status=exited" | Out-Null
Write-Host "✓ Exited containers removed" -ForegroundColor Green

# Remove unused images (keep only slim and active images)
Write-Host "`n[3/4] Removing unused images..." -ForegroundColor Yellow
docker image prune -a -f --filter "label!=keep" 2>&1 | Out-Null
Write-Host "✓ Unused images removed" -ForegroundColor Green

# Clear build cache
Write-Host "`n[4/4] Clearing build cache..." -ForegroundColor Yellow
docker builder prune -a -f 2>&1 | Out-Null
Write-Host "✓ Build cache cleared" -ForegroundColor Green

# Show final stats
Write-Host "`n" -ForegroundColor Cyan
docker system df | Format-Table -AutoSize

Write-Host "`n✓ Cleanup complete!" -ForegroundColor Green
Write-Host "Start Dream Journal with: docker-compose -f docker-compose.dream-journal.yml up -d" -ForegroundColor Cyan
