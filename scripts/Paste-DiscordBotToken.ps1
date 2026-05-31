<#
.SYNOPSIS
    Secure paste-in CLI for Discord bot credentials. Hides token during input.
.DESCRIPTION
    Prompts for Discord bot token (masked), guild ID, and channel ID.
    Validates the token live against Discord API before saving to .env.discord.
    Clears any stale cached token from the current process first.
.EXAMPLE
    .\scripts\Paste-DiscordBotToken.ps1
#>
$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$envFile = Join-Path $repoRoot ".env.discord"

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

function Read-SecureToken {
    param([string]$Prompt)
    Write-Output ""
    Write-Output $Prompt
    Write-Output "(paste and press Enter - input is hidden)"
    $secure = Read-Host -Prompt "Token" -AsSecureString
    $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    $plain = [Runtime.InteropServices.Marshal]::PtrToStringAuto($ptr)
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
    return $plain.Trim()
}

function Read-GuildOrChannelId {
    param([string]$Prompt)
    while ($true) {
        $value = Read-Host -Prompt $Prompt
        $value = $value.Trim()
        if ($value -match '^\d{10,}$') { return $value }
        if (-not $value) { return "" }
        Write-Output "Invalid: Discord snowflake IDs are 17-20 digit numbers."
    }
}

# Step 1: Clear stale token from THIS process
$env:DISCORD_BOT_TOKEN = ""
$env:LANTERN_DISCORD_GUILD_ID = ""
$env:LANTERN_DISCORD_CHANNEL_ID = ""
Write-Output "Cleared cached Discord env vars from current process."

# Step 2: Paste token securely
$token = Read-SecureToken -Prompt "=== Paste your Discord Bot Token ==="
if (-not $token) {
    throw "Token is required."
}

# Step 3: Validate token live against Discord
Write-Output ""
Write-Output "Validating token against Discord API..."
$self = Invoke-DiscordGet -Path "/users/@me" -BotToken $token
if (-not $self.ok) {
    Write-Output ""
    Write-Output "ERROR: Token invalid (HTTP $($self.code))."
    Write-Output "Get a fresh token at: https://discord.com/developers/applications"
    exit 1
}
$bot = $self.body | ConvertFrom-Json
Write-Output "Token OK. Bot identity: $($bot.username)"

# Step 4: Guild ID
$guildId = Read-GuildOrChannelId -Prompt "Paste your Discord Server (Guild) ID"
if ($guildId) {
    $guild = Invoke-DiscordGet -Path "/guilds/$guildId" -BotToken $token
    if ($guild.ok) {
        $g = $guild.body | ConvertFrom-Json
        Write-Output "Guild OK: $($g.name)"
    } else {
        Write-Output "Guild check: $($guild.code) — bot may not be invited yet."
        Write-Output "Invite: https://discord.com/oauth2/authorize?client_id=$($bot.id)&permissions=3145728&scope=bot"
    }
}

# Step 5: Channel ID
$channelId = Read-GuildOrChannelId -Prompt "Paste your Discord Text Channel ID"
if ($channelId) {
    $chan = Invoke-DiscordGet -Path "/channels/$channelId" -BotToken $token
    if ($chan.ok) {
        $c = $chan.body | ConvertFrom-Json
        Write-Output "Channel OK: #$($c.name)"
    } else {
        Write-Output "Channel check: $($chan.code)"
    }
}

# Step 6: Voice channel
$voice = Read-Host -Prompt "Voice channel name for Lounge [Lounge]"
if (-not $voice) { $voice = "Lounge" }

# Step 7: Write .env.discord
$lines = @(
    "# Lantern Discord Bot Environment - generated $(Get-Date -Format o)",
    "DISCORD_BOT_TOKEN=`"$token`"",
    "LANTERN_DISCORD_GUILD_ID=$guildId",
    "LANTERN_DISCORD_CHANNEL_ID=$channelId",
    "LANTERN_VOICE_CHANNEL=$voice"
)
$lines | Set-Content -Path $envFile -Encoding UTF8

# Step 8: Set in current session
$env:DISCORD_BOT_TOKEN = $token
$env:LANTERN_DISCORD_GUILD_ID = $guildId
$env:LANTERN_DISCORD_CHANNEL_ID = $channelId
$env:LANTERN_VOICE_CHANNEL = $voice

Write-Output ""
Write-Output "=== Saved to $envFile ==="
Write-Output ""
Write-Output "Start the bot with:"
Write-Output "  .\scripts\Start-DiscordLoungeBot.ps1 -EnableVoice -EnableRadio"
Write-Output ""
Write-Output "Then in Discord type:"
Write-Output "  !lantern-join-lounge"
Write-Output "  !lantern-radio"
