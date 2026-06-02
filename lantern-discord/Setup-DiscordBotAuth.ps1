<#
.SYNOPSIS
Discord Lounge Bot authentication setup.

.DESCRIPTION
Interactive helper that validates a Discord bot token, discovers a guild and
channels, and writes a local .env file for the Lounge bot workflow.

.PARAMETER Token
Optional bot token. If omitted, the script prompts securely.

.PARAMETER OutputPath
Directory where the generated .env file should be written.

.PARAMETER TestGuildId
Optional guild ID to prefer during discovery.

.PARAMETER ValidateOnly
Validate the token and stop before discovery / file generation.

.PARAMETER ShowOAuthHelp
Print Discord Developer Portal setup steps and exit.
#>

param(
    [string]$Token,
    [string]$OutputPath = (Get-Location),
    [string]$TestGuildId,
    [switch]$ValidateOnly,
    [switch]$ShowOAuthHelp
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$DiscordApiBase = "https://discordapp.com/api/v10"

function Write-Header {
    param([string]$Message)
    Write-Host ("`n" + ("=" * 70)) -ForegroundColor Cyan
    Write-Host $Message -ForegroundColor Cyan
    Write-Host ("=" * 70) -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "[OK] $Message" -ForegroundColor Green
}

function Write-Warn {
    param([string]$Message)
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function Write-Failure {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Get-TokenInteractively {
    Write-Host "`nPaste your Discord bot token (hidden input):" -ForegroundColor Yellow
    $secure = Read-Host -AsSecureString
    $ptr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    try {
        return [System.Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr).Trim()
    }
    finally {
        if ($ptr -ne [IntPtr]::Zero) {
            [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
        }
    }
}

function New-DiscordHeaders {
    param([Parameter(Mandatory = $true)][string]$BotToken)
    @{
        Authorization = "Bot $BotToken"
        "Content-Type" = "application/json"
    }
}

function Invoke-DiscordApi {
    param(
        [Parameter(Mandatory = $true)][string]$BotToken,
        [Parameter(Mandatory = $true)][string]$Path
    )

    Invoke-RestMethod -Uri "$DiscordApiBase/$Path" -Method Get -Headers (New-DiscordHeaders -BotToken $BotToken) -TimeoutSec 10 -ErrorAction Stop
}

function Validate-DiscordToken {
    param([Parameter(Mandatory = $true)][string]$BotToken)

    Write-Header "Validating Discord Bot Token"

    if ([string]::IsNullOrWhiteSpace($BotToken)) {
        Write-Failure "Token is empty."
        return $null
    }

    try {
        $response = Invoke-DiscordApi -BotToken $BotToken -Path "users/@me"
        Write-Success "Token validated successfully"
        Write-Host "Bot ID: $($response.id)" -ForegroundColor Green
        Write-Host "Bot Username: $($response.username)#$($response.discriminator)" -ForegroundColor Green
        return $response
    }
    catch {
        Write-Failure "Token validation failed: $($_.Exception.Message)"
        return $null
    }
}

function Select-Guild {
    param(
        [Parameter(Mandatory = $true)]$Guilds,
        [string]$PreferredGuildId
    )

    if ($PreferredGuildId) {
        $match = $Guilds | Where-Object { $_.id -eq $PreferredGuildId } | Select-Object -First 1
        if ($match) {
            Write-Success "Using provided guild ID: $PreferredGuildId"
            return $match
        }
        Write-Warn "Provided guild ID was not found. Falling back to interactive selection."
    }

    for ($i = 0; $i -lt $Guilds.Count; $i++) {
        Write-Host "[$i] $($Guilds[$i].name) (ID: $($Guilds[$i].id))" -ForegroundColor Yellow
    }

    $selection = Read-Host "Enter guild number (or press Enter for 0)"
    if ([string]::IsNullOrWhiteSpace($selection)) {
        return $Guilds[0]
    }

    $index = 0
    if ([int]::TryParse($selection, [ref]$index) -and $index -ge 0 -and $index -lt $Guilds.Count) {
        return $Guilds[$index]
    }

    Write-Warn "Invalid selection. Using the first guild."
    return $Guilds[0]
}

function Select-Channel {
    param(
        [Parameter(Mandatory = $true)]$Channels,
        [Parameter(Mandatory = $true)][string]$Prompt
    )

    for ($i = 0; $i -lt $Channels.Count; $i++) {
        Write-Host "[$i] $($Channels[$i].name) (ID: $($Channels[$i].id))" -ForegroundColor Yellow
    }

    $selection = Read-Host $Prompt
    if ([string]::IsNullOrWhiteSpace($selection)) {
        return $Channels[0]
    }

    $index = 0
    if ([int]::TryParse($selection, [ref]$index) -and $index -ge 0 -and $index -lt $Channels.Count) {
        return $Channels[$index]
    }

    Write-Warn "Invalid selection. Using the first option."
    return $Channels[0]
}

function Discover-GuildAndChannels {
    param(
        [Parameter(Mandatory = $true)][string]$BotToken,
        [string]$GuildId
    )

    Write-Header "Discovering Guilds and Channels"

    try {
        $guilds = @(Invoke-DiscordApi -BotToken $BotToken -Path "users/@me/guilds")
        if ($guilds.Count -eq 0) {
            Write-Failure "Bot is not in any guilds."
            return $null
        }

        Write-Host "Guilds found: $($guilds.Count)" -ForegroundColor Cyan
        $targetGuild = Select-Guild -Guilds $guilds -PreferredGuildId $GuildId
        Write-Success "Selected guild: $($targetGuild.name) (ID: $($targetGuild.id))"

        $channels = @(Invoke-DiscordApi -BotToken $BotToken -Path "guilds/$($targetGuild.id)/channels")
        $textChannels = @($channels | Where-Object { $_.type -eq 0 })
        $voiceChannels = @($channels | Where-Object { $_.type -eq 2 })

        if ($textChannels.Count -eq 0) {
            Write-Failure "No text channels found in the selected guild."
            return $null
        }

        if ($voiceChannels.Count -eq 0) {
            Write-Failure "No voice channels found in the selected guild."
            return $null
        }

        Write-Host "`nText Channels:" -ForegroundColor Cyan
        $botChannel = Select-Channel -Channels $textChannels -Prompt "Enter text channel number (or press Enter for 0)"

        Write-Host "`nVoice Channels:" -ForegroundColor Cyan
        $voiceChannel = Select-Channel -Channels $voiceChannels -Prompt "Enter voice channel number (or press Enter for 0)"

        Write-Success "Selected text channel: #$($botChannel.name) (ID: $($botChannel.id))"
        Write-Success "Selected voice channel: $($voiceChannel.name) (ID: $($voiceChannel.id))"

        return @{
            GuildId = [string]$targetGuild.id
            GuildName = [string]$targetGuild.name
            ChannelId = [string]$botChannel.id
            ChannelName = [string]$botChannel.name
            VoiceChannelId = [string]$voiceChannel.id
            VoiceChannelName = [string]$voiceChannel.name
        }
    }
    catch {
        Write-Failure "Failed to discover guilds/channels: $($_.Exception.Message)"
        return $null
    }
}

function Generate-EnvFile {
    param(
        [Parameter(Mandatory = $true)][string]$BotToken,
        [Parameter(Mandatory = $true)][hashtable]$GuildInfo,
        [Parameter(Mandatory = $true)][string]$TargetDirectory
    )

    Write-Header "Generating Environment Configuration"

    if (-not (Test-Path $TargetDirectory)) {
        New-Item -ItemType Directory -Path $TargetDirectory -Force | Out-Null
    }

    $envPath = Join-Path $TargetDirectory ".env"
    $envContent = @"
# Discord Lounge Bot Configuration
# Generated: $(Get-Date -Format 'o')

DISCORD_BOT_TOKEN=$BotToken
LANTERN_DISCORD_GUILD_ID=$($GuildInfo.GuildId)
LANTERN_DISCORD_GUILD_NAME=$($GuildInfo.GuildName)
LANTERN_DISCORD_CHANNEL_ID=$($GuildInfo.ChannelId)
LANTERN_DISCORD_CHANNEL_NAME=$($GuildInfo.ChannelName)
LANTERN_VOICE_CHANNEL_ID=$($GuildInfo.VoiceChannelId)
LANTERN_VOICE_CHANNEL_NAME=$($GuildInfo.VoiceChannelName)
LANTERN_STATUS_URL=http://127.0.0.1:5001/api/status
LANTERN_DISCORD_ENABLE_VOICE=false
LANTERN_DISCORD_ENABLE_RADIO=false
LANTERN_RADIO_URL=
GENERATION_TIMESTAMP=$(Get-Date -Format 'o')
GENERATION_HOSTNAME=$env:COMPUTERNAME
"@

    Set-Content -Path $envPath -Value $envContent -Encoding UTF8
    Write-Success "Environment file created: $envPath"
    return $envPath
}

function Show-OAuthFlow {
    Write-Header "Discord OAuth2 Bot Token Acquisition"
    Write-Host @"
If you do not have a bot token yet:

1. Open the Discord Developer Portal:
   https://discord.com/developers/applications

2. Create a new application and add a bot.

3. Copy the bot token from the Bot section.
   WARNING: never share this token publicly.

4. Open OAuth2 -> URL Generator.

5. Select the 'bot' scope and the permissions you need.

6. Use the generated URL to add the bot to your server.

7. Return here and rerun this script.

Test server invite:
https://discord.gg/xmsbPjMGm
"@
}

function Main {
    Write-Header "Discord Lounge Bot Authentication Setup"

    if ($ShowOAuthHelp) {
        Show-OAuthFlow
        return
    }

    if ([string]::IsNullOrWhiteSpace($Token)) {
        Write-Host "Token source options:" -ForegroundColor Cyan
        Write-Host "1. Paste token interactively" -ForegroundColor Yellow
        Write-Host "2. Read from DISCORD_BOT_TOKEN env var" -ForegroundColor Yellow
        Write-Host "3. Show OAuth flow" -ForegroundColor Yellow

        $choice = Read-Host "Choose option (1-3)"
        switch ($choice) {
            "2" {
                $Token = $env:DISCORD_BOT_TOKEN
                if ([string]::IsNullOrWhiteSpace($Token)) {
                    Write-Failure "DISCORD_BOT_TOKEN is not set."
                    return
                }
            }
            "3" {
                Show-OAuthFlow
                $Token = Get-TokenInteractively
            }
            default {
                $Token = Get-TokenInteractively
            }
        }
    }

    $botInfo = Validate-DiscordToken -BotToken $Token
    if (-not $botInfo) {
        return
    }

    if ($ValidateOnly) {
        Write-Success "Token validation complete."
        return
    }

    $guildInfo = Discover-GuildAndChannels -BotToken $Token -GuildId $TestGuildId
    if (-not $guildInfo) {
        return
    }

    $envPath = Generate-EnvFile -BotToken $Token -GuildInfo $guildInfo -TargetDirectory $OutputPath

    Write-Header "Setup Complete"
    Write-Success "Configuration ready for bot deployment"
    Write-Host "`nNext steps:" -ForegroundColor Cyan
    Write-Host "1. Load .env into your current shell if needed." -ForegroundColor Yellow
    Write-Host "2. Run .\Test-DiscordToken.ps1 to recheck access." -ForegroundColor Yellow
    Write-Host "3. Run deploy-discord-bot.ps1 to set env vars, health check, and start the bot." -ForegroundColor Yellow
    Write-Host "`nWARNING: Keep .env secure - it contains your bot token." -ForegroundColor Red
    Write-Host "Generated file: $envPath" -ForegroundColor Gray
}

Main
