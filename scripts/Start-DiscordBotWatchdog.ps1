<#
.SYNOPSIS
Discord Bot Watchdog — Keep Lantern Discord bot running 24/7

.DESCRIPTION
Monitors Discord bot process and restarts it if it crashes.
Runs in persistent terminal window. Logs all activity to ~/.lantern/logs/discord-bot.log

.PARAMETER BotScript
Path to bot_v2.py (default: $REPO_ROOT/src/discord_lounge_bot/bot_v2.py)

.PARAMETER LogDir
Log directory (default: ~/.lantern/logs)

.PARAMETER RestartDelay
Seconds to wait before restarting after crash (default: 5)

.PARAMETER CheckInterval
Seconds between health checks (default: 30)

.NOTES
Author: Founder
Generated: 2026-06-01
Status: Production
#>

param(
    [string]$BotScript = $null,
    [string]$LogDir = $null,
    [int]$RestartDelay = 5,
    [int]$CheckInterval = 30
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Continue"

# ── Configuration ──
$REPO_ROOT = (git rev-parse --show-toplevel) -replace "\\", "/"
$BotScript = if ($BotScript) { $BotScript } else { "$REPO_ROOT/src/discord_lounge_bot/bot_v2.py" }
$LogDir = if ($LogDir) { $LogDir } else { "$env:USERPROFILE/.lantern/logs" }
$LogFile = "$LogDir/discord-bot.log"
$PidFile = "$LogDir/discord-bot.pid"

# Ensure directories exist
New-Item -ItemType Directory -Path $LogDir -Force | Out-Null

# Load environment variables
$EnvFile = "$env:USERPROFILE/.lantern/discord.env"
if (Test-Path $EnvFile) {
    Get-Content $EnvFile | ForEach-Object {
        if ($_ -and !$_.StartsWith("#")) {
            $parts = $_ -split "=", 2
            if ($parts.Count -eq 2) {
                [Environment]::SetEnvironmentVariable($parts[0].Trim(), $parts[1].Trim())
            }
        }
    }
}

function Write-Log {
    param([string]$Message)
    $timestamp = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
    $logEntry = "[$timestamp] $Message"
    Write-Host $logEntry
    Add-Content -Path $LogFile -Value $logEntry
}

function Start-Bot {
    Write-Log "Starting Discord bot: $BotScript"
    try {
        $process = Start-Process `
            -FilePath "python" `
            -ArgumentList $BotScript `
            -NoNewWindow `
            -PassThru `
            -ErrorAction Stop

        if ($process) {
            $process.Id | Out-File -FilePath $PidFile -Force
            Write-Log "Bot started with PID $($process.Id)"
            return $process
        } else {
            Write-Log "ERROR: Failed to start bot process"
            return $null
        }
    } catch {
        Write-Log "ERROR starting bot: $_"
        return $null
    }
}

function Get-BotProcess {
    $pidContent = Get-Content $PidFile -ErrorAction SilentlyContinue
    if ($pidContent) {
        try {
            $process = Get-Process -Id ([int]$pidContent) -ErrorAction SilentlyContinue
            return $process
        } catch {
            return $null
        }
    }
    return $null
}

function Check-Bot-Health {
    $process = Get-BotProcess
    if ($process -and !$process.HasExited) {
        return $true
    } else {
        return $false
    }
}

# ── Main Watchdog Loop ──
Write-Log "Discord Bot Watchdog started"
Write-Log "Bot script: $BotScript"
Write-Log "Log file: $LogFile"
Write-Log "Check interval: ${CheckInterval}s"
Write-Log "Restart delay: ${RestartDelay}s"

$restartCount = 0
$lastRestart = Get-Date

while ($true) {
    $isHealthy = Check-Bot-Health

    if (-not $isHealthy) {
        $restartCount++
        $elapsedSeconds = (Get-Date) - $lastRestart | Select-Object -ExpandProperty TotalSeconds
        Write-Log "Bot is not running (restart #$restartCount, elapsed: ${elapsedSeconds}s)"

        Write-Log "Waiting ${RestartDelay}s before restart..."
        Start-Sleep -Seconds $RestartDelay

        $botProcess = Start-Bot
        if ($botProcess) {
            $lastRestart = Get-Date
        } else {
            Write-Log "ERROR: Failed to restart bot, will retry in ${CheckInterval}s"
        }
    }

    Start-Sleep -Seconds $CheckInterval
}
