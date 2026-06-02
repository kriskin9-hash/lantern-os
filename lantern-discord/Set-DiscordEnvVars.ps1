<#
.SYNOPSIS
Set Discord bot environment variables from a bot token.

.PARAMETER Token
Discord bot token.

.PARAMETER GuildId
Optional guild ID. If omitted, the script will try to auto-discover a Lantern
guild.

.PARAMETER ChannelId
Optional text channel ID.

.PARAMETER VoiceChannelId
Optional voice channel ID.

.PARAMETER Permanent
Persist discovered values into the current user's environment variables.
#>

param(
    [Parameter(Mandatory = $true)][string]$Token,
    [string]$GuildId,
    [string]$ChannelId,
    [string]$VoiceChannelId,
    [switch]$Permanent
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$DiscordApiBase = "https://discordapp.com/api/v10"
$headers = @{
    Authorization = "Bot $Token"
    "Content-Type" = "application/json"
}

function Write-Header {
    param([string]$Message)
    Write-Host ("`n" + ("=" * 70)) -ForegroundColor Cyan
    Write-Host $Message -ForegroundColor Cyan
    Write-Host ("=" * 70) -ForegroundColor Cyan
}

function Invoke-DiscordApi {
    param([Parameter(Mandatory = $true)][string]$Path)
    Invoke-RestMethod -Uri "$DiscordApiBase/$Path" -Method Get -Headers $headers -TimeoutSec 10
}

Write-Header "Discord Bot Environment Setup"

$env:DISCORD_BOT_TOKEN = $Token
Write-Host "`n[OK] DISCORD_BOT_TOKEN set for this session" -ForegroundColor Green

if ($GuildId) {
    $env:LANTERN_DISCORD_GUILD_ID = $GuildId
    Write-Host "[OK] LANTERN_DISCORD_GUILD_ID = $GuildId" -ForegroundColor Green
}

if ($ChannelId) {
    $env:LANTERN_DISCORD_CHANNEL_ID = $ChannelId
    Write-Host "[OK] LANTERN_DISCORD_CHANNEL_ID = $ChannelId" -ForegroundColor Green
}

if ($VoiceChannelId) {
    $env:LANTERN_VOICE_CHANNEL_ID = $VoiceChannelId
    Write-Host "[OK] LANTERN_VOICE_CHANNEL_ID = $VoiceChannelId" -ForegroundColor Green
}

Write-Host "`nTesting token..." -ForegroundColor Cyan
try {
    $resp = Invoke-DiscordApi -Path "users/@me"
    Write-Host "[OK] Token valid - Bot: $($resp.username)#$($resp.discriminator)" -ForegroundColor Green
}
catch {
    Write-Error "Token invalid: $($_.Exception.Message)"
    exit 1
}

if (-not $GuildId) {
    Write-Host "`nDiscovering guilds..." -ForegroundColor Yellow
    try {
        $guilds = @(Invoke-DiscordApi -Path "users/@me/guilds")

        Write-Host "Guilds found:" -ForegroundColor Yellow
        for ($i = 0; $i -lt $guilds.Count; $i++) {
            Write-Host "  [$i] $($guilds[$i].name) (ID: $($guilds[$i].id))"
        }

        $lanternGuild = $guilds | Where-Object { $_.name -like "*Lantern*" } | Select-Object -First 1
        if ($lanternGuild) {
            $env:LANTERN_DISCORD_GUILD_ID = [string]$lanternGuild.id
            Write-Host "`n[OK] Auto-discovered Lantern guild: $($lanternGuild.name)" -ForegroundColor Green
            Write-Host "  LANTERN_DISCORD_GUILD_ID = $($lanternGuild.id)" -ForegroundColor Green

            $channels = @(Invoke-DiscordApi -Path "guilds/$($lanternGuild.id)/channels")
            $textChannels = @($channels | Where-Object { $_.type -eq 0 })
            $voiceChannels = @($channels | Where-Object { $_.type -eq 2 })

            Write-Host "`nText Channels:" -ForegroundColor Yellow
            for ($i = 0; $i -lt $textChannels.Count; $i++) {
                Write-Host "  [$i] #$($textChannels[$i].name) (ID: $($textChannels[$i].id))"
            }

            Write-Host "`nVoice Channels:" -ForegroundColor Yellow
            for ($i = 0; $i -lt $voiceChannels.Count; $i++) {
                Write-Host "  [$i] $($voiceChannels[$i].name) (ID: $($voiceChannels[$i].id))"
            }

            if (-not $ChannelId) {
                $generalText = $textChannels | Where-Object { $_.name -like "*general*" -or $_.name -like "*bot*" } | Select-Object -First 1
                if ($generalText) {
                    $env:LANTERN_DISCORD_CHANNEL_ID = [string]$generalText.id
                    Write-Host "`n[OK] Auto-set LANTERN_DISCORD_CHANNEL_ID = $($generalText.id) (#$($generalText.name))" -ForegroundColor Green
                }
            }

            if (-not $VoiceChannelId) {
                $voiceLounge = $voiceChannels | Where-Object { $_.name -like "*lounge*" -or $_.name -like "*voice*" } | Select-Object -First 1
                if ($voiceLounge) {
                    $env:LANTERN_VOICE_CHANNEL_ID = [string]$voiceLounge.id
                    Write-Host "[OK] Auto-set LANTERN_VOICE_CHANNEL_ID = $($voiceLounge.id) ($($voiceLounge.name))" -ForegroundColor Green
                }
            }
        }
    }
    catch {
        Write-Warning "Could not auto-discover guilds/channels: $($_.Exception.Message)"
    }
}

Write-Header "Current Environment Variables"
$vars = @(
    "DISCORD_BOT_TOKEN",
    "LANTERN_DISCORD_GUILD_ID",
    "LANTERN_DISCORD_CHANNEL_ID",
    "LANTERN_VOICE_CHANNEL_ID"
)

foreach ($var in $vars) {
    $value = Get-Item -Path "env:$var" -ErrorAction SilentlyContinue
    if ($value) {
        $display = if ($var -like "*TOKEN*") { "***SET***" } else { $value.Value }
        Write-Host "$var = $display" -ForegroundColor Green
    }
    else {
        Write-Host "$var = [NOT SET]" -ForegroundColor Yellow
    }
}

if ($Permanent) {
    Write-Host "`nMaking environment variables permanent..." -ForegroundColor Yellow
    [Environment]::SetEnvironmentVariable("DISCORD_BOT_TOKEN", $env:DISCORD_BOT_TOKEN, "User")
    [Environment]::SetEnvironmentVariable("LANTERN_DISCORD_GUILD_ID", $env:LANTERN_DISCORD_GUILD_ID, "User")
    [Environment]::SetEnvironmentVariable("LANTERN_DISCORD_CHANNEL_ID", $env:LANTERN_DISCORD_CHANNEL_ID, "User")
    [Environment]::SetEnvironmentVariable("LANTERN_VOICE_CHANNEL_ID", $env:LANTERN_VOICE_CHANNEL_ID, "User")
    Write-Host "[OK] Environment variables saved to user profile" -ForegroundColor Green
    Write-Host "Restart PowerShell to load the permanent values in new terminals." -ForegroundColor Gray
}

Write-Host "`n[OK] Setup complete" -ForegroundColor Green
