param(
    [string]$Python = "python",
    [string]$Token = "",
    [string]$GuildId = "",
    [string]$ChannelId = "",
    [string]$VoiceChannel = "",
    [string]$EnvFile = "",
    [switch]$NoHealthCheck,
    [switch]$EnableVoice,
    [switch]$EnableRadio
)

$ErrorActionPreference = "Stop"

$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$botPath = Join-Path $root "src/discord_lounge_bot/bot.py"
$healthPath = Join-Path $root "scripts/Test-DiscordBotHealth.ps1"
$defaultEnvFile = Join-Path $root ".env.discord"

# Load .env.discord if it exists and no explicit overrides
$envSource = if ($EnvFile) { $EnvFile } else { $defaultEnvFile }
if (Test-Path $envSource) {
    Get-Content $envSource | ForEach-Object {
        $line = $_.Trim()
        if ($line -match "^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$") {
            $key = $matches[1]
            $val = $matches[2].Trim().Trim("'").Trim('"')
            if (-not [Environment]::GetEnvironmentVariable($key)) {
                [Environment]::SetEnvironmentVariable($key, $val, "Process") | Out-Null
            }
        }
    }
    Write-Output "Loaded env from: $envSource"
}

# CLI overrides take precedence
if ($Token) { $env:DISCORD_BOT_TOKEN = $Token }
if ($GuildId) { $env:LANTERN_DISCORD_GUILD_ID = $GuildId }
if ($ChannelId) { $env:LANTERN_DISCORD_CHANNEL_ID = $ChannelId }
if ($VoiceChannel) { $env:LANTERN_VOICE_CHANNEL = $VoiceChannel }
if ($EnableVoice) { $env:LANTERN_DISCORD_ENABLE_VOICE = "true" }
if ($EnableRadio) { $env:LANTERN_DISCORD_ENABLE_RADIO = "true" }

if (-not (Test-Path -LiteralPath $botPath)) {
    throw "Missing bot runtime: $botPath"
}

if (-not $NoHealthCheck) {
    & powershell -NoProfile -ExecutionPolicy Bypass -File $healthPath
    if ($LASTEXITCODE -ne 0) {
        throw "Discord bot health check failed. Fix failures before launch. Run .\scripts\Set-DiscordBotToken.ps1 to reconfigure."
    }
}

Write-Output "Starting Discord lounge bot runtime..."
Write-Output "Path: $botPath"
Write-Output "Voice enabled: $($env:LANTERN_DISCORD_ENABLE_VOICE)"
Write-Output "Radio enabled: $($env:LANTERN_DISCORD_ENABLE_RADIO)"
Write-Output "Press Ctrl+C to stop."

& $Python $botPath
exit $LASTEXITCODE
