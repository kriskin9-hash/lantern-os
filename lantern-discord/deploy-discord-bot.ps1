<#
.SYNOPSIS
Deploy Discord Lounge Bot - full setup and startup.

.DESCRIPTION
Validates the configured bot token, discovers the Lantern guild and channels,
sets the required environment variables, runs the health check, and starts the
bot from the orchestrator repo.

.EXAMPLE
powershell -NoProfile -ExecutionPolicy Bypass -File .\deploy-discord-bot.ps1
#>

$ErrorActionPreference = "Stop"

$DiscordApiBase = "https://discordapp.com/api/v10"

# ==================== CONFIG ====================
$token = "PASTE_NEW_TOKEN_HERE"
$guildName = "*Lantern*"
$textChanPattern = @("*general*", "*bot*")
$voiceChanPattern = @("*lounge*", "*voice*")
$orchDir = "C:\Users\alexp\Documents\gm-agent-orchestrator"

function Write-SectionHeader {
    param([string]$Message)
    Write-Host ("`n" + ("=" * 70)) -ForegroundColor Cyan
    Write-Host $Message -ForegroundColor Cyan
    Write-Host ("=" * 70) -ForegroundColor Cyan
}

function Invoke-DiscordApi {
    param(
        [Parameter(Mandatory = $true)][string]$Path
    )

    $headers = @{
        Authorization = "Bot $token"
        "Content-Type" = "application/json"
    }

    Invoke-RestMethod -Uri "$DiscordApiBase/$Path" -Method Get -Headers $headers -TimeoutSec 10
}

Write-SectionHeader "LANTERN DISCORD BOT - DEPLOYMENT"

# ==================== STEP 1: VALIDATE TOKEN ====================
Write-Host "`n[1/5] Validating bot token..." -ForegroundColor Yellow

try {
    $botInfo = Invoke-DiscordApi -Path "users/@me"
    Write-Host "[OK] Bot verified: $($botInfo.username)#$($botInfo.discriminator)" -ForegroundColor Green
}
catch {
    Write-Error "[ERROR] Token invalid: $($_.Exception.Message)"
    exit 1
}

# ==================== STEP 2: AUTO-DISCOVER GUILD & CHANNELS ====================
Write-Host "`n[2/5] Discovering Lantern guild and channels..." -ForegroundColor Yellow

try {
    $guilds = @(Invoke-DiscordApi -Path "users/@me/guilds")
    $lanternGuild = $guilds | Where-Object { $_.name -like $guildName } | Select-Object -First 1

    if (-not $lanternGuild) {
        throw "Guild '$guildName' not found. Available guilds: $($guilds.name -join ', ')"
    }

    Write-Host "[OK] Guild: $($lanternGuild.name) (ID: $($lanternGuild.id))" -ForegroundColor Green

    $channels = @(Invoke-DiscordApi -Path "guilds/$($lanternGuild.id)/channels")
    $textChannels = @($channels | Where-Object { $_.type -eq 0 })
    $voiceChannels = @($channels | Where-Object { $_.type -eq 2 })

    if ($textChannels.Count -eq 0) {
        throw "No text channels were found in guild '$($lanternGuild.name)'."
    }

    if ($voiceChannels.Count -eq 0) {
        throw "No voice channels were found in guild '$($lanternGuild.name)'."
    }

    $textChannel = $null
    foreach ($pattern in $textChanPattern) {
        $textChannel = $textChannels | Where-Object { $_.name -like $pattern } | Select-Object -First 1
        if ($textChannel) { break }
    }
    if (-not $textChannel) {
        $textChannel = $textChannels[0]
    }

    $voiceChannel = $null
    foreach ($pattern in $voiceChanPattern) {
        $voiceChannel = $voiceChannels | Where-Object { $_.name -like $pattern } | Select-Object -First 1
        if ($voiceChannel) { break }
    }
    if (-not $voiceChannel) {
        $voiceChannel = $voiceChannels[0]
    }

    Write-Host "[OK] Text channel: #$($textChannel.name) (ID: $($textChannel.id))" -ForegroundColor Green
    Write-Host "[OK] Voice channel: $($voiceChannel.name) (ID: $($voiceChannel.id))" -ForegroundColor Green
}
catch {
    Write-Error "[ERROR] Channel discovery failed: $($_.Exception.Message)"
    exit 1
}

# ==================== STEP 3: SET ENVIRONMENT VARIABLES ====================
Write-Host "`n[3/5] Setting environment variables..." -ForegroundColor Yellow

$env:DISCORD_BOT_TOKEN = $token
$env:LANTERN_DISCORD_GUILD_ID = [string]$lanternGuild.id
$env:LANTERN_DISCORD_CHANNEL_ID = [string]$textChannel.id
$env:LANTERN_VOICE_CHANNEL_ID = [string]$voiceChannel.id

[Environment]::SetEnvironmentVariable("DISCORD_BOT_TOKEN", $token, "User")
[Environment]::SetEnvironmentVariable("LANTERN_DISCORD_GUILD_ID", [string]$lanternGuild.id, "User")
[Environment]::SetEnvironmentVariable("LANTERN_DISCORD_CHANNEL_ID", [string]$textChannel.id, "User")
[Environment]::SetEnvironmentVariable("LANTERN_VOICE_CHANNEL_ID", [string]$voiceChannel.id, "User")

Write-Host "[OK] Environment variables set (permanent)" -ForegroundColor Green

# ==================== STEP 4: HEALTH CHECK ====================
Write-Host "`n[4/5] Running health check..." -ForegroundColor Yellow

$healthScript = Join-Path $orchDir "scripts\Test-DiscordBotHealth.ps1"
if (Test-Path $healthScript) {
    & $healthScript
}
else {
    Write-Warning "Health check script not found at $healthScript (skipping)"
}

# ==================== STEP 5: START BOT ====================
Write-Host "`n[5/5] Starting Discord bot..." -ForegroundColor Yellow

$startScript = Join-Path $orchDir "scripts\Start-DiscordLoungeBot.ps1"
if (Test-Path $startScript) {
    Write-Host "[OK] Launching bot..." -ForegroundColor Green
    & $startScript
}
else {
    Write-Error "[ERROR] Bot startup script not found: $startScript"
    Write-Host "Run manually: & '$startScript'" -ForegroundColor Yellow
    exit 1
}

Write-Host ("`n" + ("=" * 70)) -ForegroundColor Green
Write-Host "[OK] DISCORD BOT DEPLOYMENT COMPLETE" -ForegroundColor Green
Write-Host ("=" * 70) -ForegroundColor Green
Write-Host ""
