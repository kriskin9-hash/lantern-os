#Requires -RunAsAdministrator
<#
.SYNOPSIS
Restart Lantern OS MCP server and deploy Discord bot with environment variables.
#>

$ErrorActionPreference = "Stop"
$orchDir = "C:\Users\alexp\Documents\gm-agent-orchestrator"

Write-Host "`n" + ("=" * 70) -ForegroundColor Cyan
Write-Host "LANTERN OS - RESTART MCP SERVER + DISCORD BOT DEPLOYMENT" -ForegroundColor Cyan
Write-Host ("=" * 70) -ForegroundColor Cyan

# Step 1: Check for existing Discord env vars
Write-Host "`n[1/3] Checking Discord environment variables..." -ForegroundColor Yellow

$discordVars = @(
    "DISCORD_BOT_TOKEN",
    "LANTERN_DISCORD_GUILD_ID",
    "LANTERN_DISCORD_CHANNEL_ID",
    "LANTERN_VOICE_CHANNEL_ID"
)

$allSet = $true
foreach ($var in $discordVars) {
    $value = [Environment]::GetEnvironmentVariable($var, "User")
    if ($value) {
        $display = if ($var -eq "DISCORD_BOT_TOKEN") { "***SET***" } else { $value }
        Write-Host "  ✓ $var = $display" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $var = [NOT SET]" -ForegroundColor Yellow
        $allSet = $false
    }
}

if (-not $allSet) {
    Write-Host "`n⚠ Some Discord env vars are not set. Configure them before starting the bot." -ForegroundColor Yellow
}

# Step 2: Remove Kapture if it exists
Write-Host "`n[2/3] Cleaning up (Kapture)..." -ForegroundColor Yellow
$kaptureLocations = @(
    "D:\tmp\lantern-discord\Kapture",
    "$env:USERPROFILE\Downloads\Kapture",
    "$orchDir\Kapture"
)

foreach ($loc in $kaptureLocations) {
    if (Test-Path $loc) {
        Write-Host "  Removing: $loc" -ForegroundColor Yellow
        Remove-Item -Path $loc -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "  ✓ Removed" -ForegroundColor Green
    }
}

Write-Host "  ✓ Cleanup complete" -ForegroundColor Green

# Step 3: Restart MCP Server
Write-Host "`n[3/3] Restarting Lantern OS MCP server (port 8787)..." -ForegroundColor Yellow
Write-Host "  Starting: Start-OrchMcpServer.ps1 -NoAuth" -ForegroundColor Gray

try {
    $startScript = Join-Path $orchDir "scripts\Start-OrchMcpServer.ps1"
    if (-not (Test-Path $startScript)) {
        throw "MCP server script not found: $startScript"
    }

    # Kill existing MCP server if running
    $existingProcess = Get-Process -Name "pwsh" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*Start-OrchMcpServer*" }
    if ($existingProcess) {
        Write-Host "  Stopping existing MCP server process..." -ForegroundColor Gray
        $existingProcess | Stop-Process -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
    }

    # Start new MCP server
    & $startScript -NoAuth -Port 8787

    Write-Host "`n✓ MCP server started on http://127.0.0.1:8787" -ForegroundColor Green
    Write-Host "  Health check: http://127.0.0.1:8787/health" -ForegroundColor Gray

} catch {
    Write-Error "Failed to start MCP server: $($_.Exception.Message)"
    exit 1
}

Write-Host "`n" + ("=" * 70) -ForegroundColor Green
Write-Host "✓ LANTERN OS MCP SERVER ONLINE" -ForegroundColor Green
Write-Host ("=" * 70) -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Verify MCP server: curl http://127.0.0.1:8787/health" -ForegroundColor Gray
Write-Host "  2. If Discord env vars are set, deploy bot: .\RUN-DEPLOY.bat" -ForegroundColor Gray
Write-Host ""
