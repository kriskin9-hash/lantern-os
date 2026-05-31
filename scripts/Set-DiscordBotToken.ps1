<#
.SYNOPSIS
    Configure Discord bot token and required IDs via CLI.
.DESCRIPTION
    Interactive CLI for setting DISCORD_BOT_TOKEN, LANTERN_DISCORD_GUILD_ID,
    and LANTERN_DISCORD_CHANNEL_ID. Validates the token against Discord API
    before saving. Optionally persists to a .env file for local reuse.
.PARAMETER Token
    Discord bot token (from https://discord.com/developers/applications)
.PARAMETER GuildId
    Discord server (guild) ID where the bot lives
.PARAMETER ChannelId
    Discord text channel ID for bot commands
.PARAMETER VoiceChannel
    Voice channel name for lounge join (default: "Lounge")
.PARAMETER EnvFile
    Path to write/load .env file (default: .env.discord in repo root)
.PARAMETER ValidateOnly
    Only validate existing env vars; do not prompt or write
.EXAMPLE
    .\Set-DiscordBotToken.ps1 -Token "YOUR_BOT_TOKEN" -GuildId "123" -ChannelId "456"
    .\Set-DiscordBotToken.ps1 -ValidateOnly
#>
param(
    [string]$Token = "",
    [string]$GuildId = "",
    [string]$ChannelId = "",
    [string]$VoiceChannel = "Lounge",
    [string]$EnvFile = "",
    [switch]$ValidateOnly
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
if ([string]::IsNullOrWhiteSpace($EnvFile)) {
    $EnvFile = Join-Path $repoRoot ".env.discord"
}

function Invoke-DiscordGet {
    param([string]$Path, [string]$BotToken, [int]$Timeout = 8)
    $uri = "https://discord.com/api/v10$Path"
    $headers = @{ Authorization = "Bot $BotToken" }
    try {
        $resp = Invoke-WebRequest -Uri $uri -Headers $headers -UseBasicParsing -TimeoutSec $Timeout -Method Get
        return @{ ok = $true; code = [int]$resp.StatusCode; body = $resp.Content }
    } catch {
        $code = if ($_.Exception.Response -and $_.Exception.Response.StatusCode) {
            [int]$_.Exception.Response.StatusCode
        } else { $null }
        return @{ ok = $false; code = $code; body = $_.Exception.Message }
    }
}

function Read-EnvFile {
    param([string]$Path)
    $map = @{}
    if (Test-Path $Path) {
        Get-Content $Path | ForEach-Object {
            $line = $_.Trim()
            if ($line -match "^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$") {
                $map[$matches[1]] = $matches[2].Trim().Trim("'").Trim('"')
            }
        }
    }
    return $map
}

function Write-EnvFile {
    param([string]$Path, [hashtable]$Map)
    $timestamp = Get-Date -Format o
    $lines = @("# Lantern Discord Bot Environment - generated $timestamp")
    foreach ($key in ($Map.Keys | Sort-Object)) {
        $val = $Map[$key]
        if ($val -match "\s") { $val = '"' + $val + '"' }
        $lines += "$key=$val"
    }
    $lines | Set-Content -Path $Path -Encoding UTF8
    Write-Output "Wrote env file: $Path"
}

# Load existing env file
$envMap = Read-EnvFile -Path $EnvFile

# Check current environment + env file
$currentToken = if ($Token) { $Token } elseif ($env:DISCORD_BOT_TOKEN) { $env:DISCORD_BOT_TOKEN } elseif ($envMap["DISCORD_BOT_TOKEN"]) { $envMap["DISCORD_BOT_TOKEN"] } else { "" }
$currentGuild = if ($GuildId) { $GuildId } elseif ($env:LANTERN_DISCORD_GUILD_ID) { $env:LANTERN_DISCORD_GUILD_ID } elseif ($envMap["LANTERN_DISCORD_GUILD_ID"]) { $envMap["LANTERN_DISCORD_GUILD_ID"] } else { "" }
$currentChannel = if ($ChannelId) { $ChannelId } elseif ($env:LANTERN_DISCORD_CHANNEL_ID) { $env:LANTERN_DISCORD_CHANNEL_ID } elseif ($envMap["LANTERN_DISCORD_CHANNEL_ID"]) { $envMap["LANTERN_DISCORD_CHANNEL_ID"] } else { "" }
$currentVoice = if ($VoiceChannel) { $VoiceChannel } elseif ($env:LANTERN_VOICE_CHANNEL) { $env:LANTERN_VOICE_CHANNEL } elseif ($envMap["LANTERN_VOICE_CHANNEL"]) { $envMap["LANTERN_VOICE_CHANNEL"] } else { "Lounge" }

if ($ValidateOnly) {
    Write-Output "=== Discord Bot Token Validation ==="
    Write-Output "Token present: $(if ($currentToken) { 'yes (hidden)' } else { 'NO' })"
    Write-Output "Guild ID present: $(if ($currentGuild) { 'yes' } else { 'NO' })"
    Write-Output "Channel ID present: $(if ($currentChannel) { 'yes' } else { 'NO' })"
    Write-Output "Voice channel: $currentVoice"
    if (-not $currentToken) { exit 1 }
    $self = Invoke-DiscordGet -Path "/users/@me" -BotToken $currentToken
    if ($self.ok) {
        $body = $self.body | ConvertFrom-Json
        Write-Output "Token VALID. Bot identity: $($body.username)#$($body.discriminator)"
        if ($currentGuild) {
            $guild = Invoke-DiscordGet -Path "/guilds/$currentGuild" -BotToken $currentToken
            if ($guild.ok) {
                $gbody = $guild.body | ConvertFrom-Json
                Write-Output "Guild VALID: $($gbody.name)"
            } else {
                Write-Output "Guild INVALID (HTTP $($guild.code)): $($guild.body)"
            }
        }
        if ($currentChannel) {
            $chan = Invoke-DiscordGet -Path "/channels/$currentChannel" -BotToken $currentToken
            if ($chan.ok) {
                $cbody = $chan.body | ConvertFrom-Json
                Write-Output "Channel VALID: #$($cbody.name)"
            } else {
                Write-Output "Channel INVALID (HTTP $($chan.code)): $($chan.body)"
            }
        }
        exit 0
    } else {
        Write-Output "Token INVALID (HTTP $($self.code)): $($self.body)"
        Write-Output "Action: Go to https://discord.com/developers/applications → Bot → Reset Token"
        exit 1
    }
}

# Interactive mode
Write-Output "=== Lantern Discord Bot CLI Configuration ==="
Write-Output "Repo root: $repoRoot"
Write-Output ""

if (-not $currentToken) {
    Write-Output "No DISCORD_BOT_TOKEN found."
    Write-Output "Get one at: https://discord.com/developers/applications → Your App → Bot → Reset Token"
    $inputToken = Read-Host -Prompt "Paste your Discord bot token"
    if (-not [string]::IsNullOrWhiteSpace($inputToken)) {
        $currentToken = $inputToken.Trim()
    }
} else {
    Write-Output "Existing token found. Validating..."
}

if (-not $currentToken) {
    throw "Token is required. Cannot proceed without DISCORD_BOT_TOKEN."
}

# Validate token
$self = Invoke-DiscordGet -Path "/users/@me" -BotToken $currentToken
if (-not $self.ok) {
    Write-Output ""
    Write-Output "ERROR: Token validation failed (HTTP $($self.code))."
    Write-Output "The token is expired, revoked, or incorrect."
    Write-Output "Fix: https://discord.com/developers/applications → Bot → Reset Token"
    throw "Invalid DISCORD_BOT_TOKEN"
}

$botIdentity = $self.body | ConvertFrom-Json
Write-Output "Token VALID. Bot: $($botIdentity.username)#$($botIdentity.discriminator)"

# Guild
if (-not $currentGuild) {
    Write-Output ""
    Write-Output "Guild ID needed. Find it in Discord: Server Settings → Widget → Server ID"
    $inputGuild = Read-Host -Prompt "Paste your Discord server (guild) ID"
    if (-not [string]::IsNullOrWhiteSpace($inputGuild)) {
        $currentGuild = $inputGuild.Trim()
    }
}
if (-not $currentGuild) {
    throw "Guild ID is required."
}

$guildCheck = Invoke-DiscordGet -Path "/guilds/$currentGuild" -BotToken $currentToken
if (-not $guildCheck.ok) {
    Write-Output "WARNING: Cannot access guild (HTTP $($guildCheck.code)). Bot may not be invited to this server."
    Write-Output "Invite link: https://discord.com/oauth2/authorize?client_id=$($botIdentity.id)&permissions=3145728&scope=bot%20applications.commands"
} else {
    $gbody = $guildCheck.body | ConvertFrom-Json
    Write-Output "Guild VALID: $($gbody.name)"
}

# Channel
if (-not $currentChannel) {
    Write-Output ""
    Write-Output "Channel ID needed. In Discord: Settings → Advanced → Developer Mode ON, then right-click channel → Copy Channel ID"
    $inputChannel = Read-Host -Prompt "Paste your text channel ID"
    if (-not [string]::IsNullOrWhiteSpace($inputChannel)) {
        $currentChannel = $inputChannel.Trim()
    }
}
if (-not $currentChannel) {
    throw "Channel ID is required."
}

# Write env file
$envMap["DISCORD_BOT_TOKEN"] = $currentToken
$envMap["LANTERN_DISCORD_GUILD_ID"] = $currentGuild
$envMap["LANTERN_DISCORD_CHANNEL_ID"] = $currentChannel
$envMap["LANTERN_VOICE_CHANNEL"] = $currentVoice
Write-EnvFile -Path $EnvFile -Map $envMap

# Also set in current session
$env:DISCORD_BOT_TOKEN = $currentToken
$env:LANTERN_DISCORD_GUILD_ID = $currentGuild
$env:LANTERN_DISCORD_CHANNEL_ID = $currentChannel
$env:LANTERN_VOICE_CHANNEL = $currentVoice

Write-Output ""
Write-Output "=== Configuration Complete ==="
Write-Output "Env file: $EnvFile"
Write-Output "Current session vars updated."
Write-Output ""
Write-Output "Next: Start the bot with:"
Write-Output "  .\scripts\Start-DiscordLoungeBot.ps1"
Write-Output ""
Write-Output "Voice join command in Discord: !lantern-join-lounge"
Write-Output "Radio command (needs LANTERN_DISCORD_ENABLE_RADIO=true): !lantern-radio"
