param(
    [string]$TokenEnv = "DISCORD_BOT_TOKEN",
    [string]$GuildEnv = "LANTERN_DISCORD_GUILD_ID",
    [string]$ChannelEnv = "LANTERN_DISCORD_CHANNEL_ID",
    [string]$VoiceChannelEnv = "LANTERN_VOICE_CHANNEL",
    [string]$VoiceChannelIdEnv = "LANTERN_VOICE_CHANNEL_ID",
    [int]$TimeoutSec = 8,
    [switch]$Json
)

$ErrorActionPreference = "Stop"

function New-Check {
    param(
        [string]$Name,
        [string]$Status,
        [string]$Message
    )

    [ordered]@{
        name = $Name
        status = $Status
        message = $Message
    }
}

function Invoke-DiscordGet {
    param(
        [string]$Path,
        [string]$Token,
        [int]$Timeout
    )

    $uri = "https://discord.com/api/v10$Path"
    $headers = @{
        Authorization = "Bot $Token"
    }

    try {
        $response = Invoke-WebRequest -Uri $uri -Headers $headers -UseBasicParsing -TimeoutSec $Timeout -Method Get
        return [ordered]@{
            ok = $true
            code = [int]$response.StatusCode
            body = $response.Content
        }
    } catch {
        $statusCode = $null
        if ($_.Exception.Response -and $_.Exception.Response.StatusCode) {
            $statusCode = [int]$_.Exception.Response.StatusCode
        }
        return [ordered]@{
            ok = $false
            code = $statusCode
            body = $_.Exception.Message
        }
    }
}

function Test-PythonModule {
    param(
        [string]$Module,
        [string]$Name,
        [string]$Purpose
    )

    $python = Get-Command python -ErrorAction SilentlyContinue
    if (-not $python) {
        return New-Check -Name $Name -Status "fail" -Message "Python is not available; cannot validate $Purpose."
    }

    $code = "import importlib.util, sys; sys.exit(0 if importlib.util.find_spec('$Module') else 1)"
    & python -c $code *> $null
    if ($LASTEXITCODE -eq 0) {
        return New-Check -Name $Name -Status "pass" -Message "$Purpose dependency is installed."
    }
    return New-Check -Name $Name -Status "fail" -Message "Missing $Purpose dependency. Install repo voice deps before starting the bot."
}

$token = [Environment]::GetEnvironmentVariable($TokenEnv)
$guildId = [Environment]::GetEnvironmentVariable($GuildEnv)
$channelId = [Environment]::GetEnvironmentVariable($ChannelEnv)
$voiceChannelName = [Environment]::GetEnvironmentVariable($VoiceChannelEnv)
$voiceChannelId = [Environment]::GetEnvironmentVariable($VoiceChannelIdEnv)

$checks = New-Object System.Collections.Generic.List[object]

if ([string]::IsNullOrWhiteSpace($token)) {
    $checks.Add((New-Check -Name "token_env" -Status "fail" -Message "Missing env var '$TokenEnv'.")) | Out-Null
} else {
    $checks.Add((New-Check -Name "token_env" -Status "pass" -Message "Token env var exists (value not printed).")) | Out-Null
}

if ([string]::IsNullOrWhiteSpace($guildId)) {
    $checks.Add((New-Check -Name "guild_env" -Status "warn" -Message "Missing env var '$GuildEnv'; guild check skipped.")) | Out-Null
} else {
    $checks.Add((New-Check -Name "guild_env" -Status "pass" -Message "Guild env var exists.")) | Out-Null
}

if ([string]::IsNullOrWhiteSpace($channelId)) {
    $checks.Add((New-Check -Name "channel_env" -Status "warn" -Message "Missing env var '$ChannelEnv'; channel check skipped.")) | Out-Null
} else {
    $checks.Add((New-Check -Name "channel_env" -Status "pass" -Message "Channel env var exists.")) | Out-Null
}

$checks.Add((Test-PythonModule -Module "discord" -Name "discord_py_dependency" -Purpose "discord.py")) | Out-Null
$checks.Add((Test-PythonModule -Module "nacl" -Name "pynacl_voice_dependency" -Purpose "PyNaCl Discord voice")) | Out-Null

if (Get-Command ffmpeg -ErrorAction SilentlyContinue) {
    $checks.Add((New-Check -Name "ffmpeg_dependency" -Status "pass" -Message "ffmpeg is available on PATH for voice/radio playback.")) | Out-Null
} else {
    $checks.Add((New-Check -Name "ffmpeg_dependency" -Status "fail" -Message "Missing ffmpeg on PATH; Discord voice/radio playback cannot run.")) | Out-Null
}

if ([string]::IsNullOrWhiteSpace($voiceChannelId) -and [string]::IsNullOrWhiteSpace($voiceChannelName)) {
    $checks.Add((New-Check -Name "voice_target_env" -Status "fail" -Message "Missing '$VoiceChannelIdEnv' or '$VoiceChannelEnv'; Lounge voice target is not configured.")) | Out-Null
} elseif (-not [string]::IsNullOrWhiteSpace($voiceChannelId)) {
    $checks.Add((New-Check -Name "voice_target_env" -Status "pass" -Message "Voice channel id env var exists.")) | Out-Null
} else {
    $checks.Add((New-Check -Name "voice_target_env" -Status "pass" -Message "Voice channel name env var exists ('$voiceChannelName').")) | Out-Null
}

if (-not [string]::IsNullOrWhiteSpace($token)) {
    $self = Invoke-DiscordGet -Path "/users/@me" -Token $token -Timeout $TimeoutSec
    if ($self.ok) {
        $checks.Add((New-Check -Name "token_api_identity" -Status "pass" -Message "Discord API identity check passed.")) | Out-Null
    } else {
        $code = if ($null -eq $self.code) { "n/a" } else { [string]$self.code }
        $checks.Add((New-Check -Name "token_api_identity" -Status "fail" -Message "Discord API identity check failed (HTTP $code).")) | Out-Null
    }

    if (-not [string]::IsNullOrWhiteSpace($guildId)) {
        $guild = Invoke-DiscordGet -Path "/guilds/$guildId" -Token $token -Timeout $TimeoutSec
        if ($guild.ok) {
            $checks.Add((New-Check -Name "guild_access" -Status "pass" -Message "Bot can access guild id '$guildId'.")) | Out-Null
        } else {
            $code = if ($null -eq $guild.code) { "n/a" } else { [string]$guild.code }
            $checks.Add((New-Check -Name "guild_access" -Status "fail" -Message "Guild access failed for id '$guildId' (HTTP $code).")) | Out-Null
        }

        $channels = Invoke-DiscordGet -Path "/guilds/$guildId/channels" -Token $token -Timeout $TimeoutSec
        if ($channels.ok) {
            $parsedChannels = @($channels.body | ConvertFrom-Json)
            $voiceChannels = @($parsedChannels | Where-Object { $_.type -eq 2 -or $_.type -eq 13 })
            $matchedVoice = $null
            if (-not [string]::IsNullOrWhiteSpace($voiceChannelId)) {
                $matchedVoice = $voiceChannels | Where-Object { [string]$_.id -eq [string]$voiceChannelId } | Select-Object -First 1
            } elseif (-not [string]::IsNullOrWhiteSpace($voiceChannelName)) {
                $matchedVoice = $voiceChannels | Where-Object { [string]::Equals($_.name, $voiceChannelName, [System.StringComparison]::OrdinalIgnoreCase) } | Select-Object -First 1
            }

            if ($matchedVoice) {
                $checks.Add((New-Check -Name "voice_channel_access" -Status "pass" -Message "Bot can see voice channel '$($matchedVoice.name)'.")) | Out-Null
            } elseif (-not [string]::IsNullOrWhiteSpace($voiceChannelId) -or -not [string]::IsNullOrWhiteSpace($voiceChannelName)) {
                $target = if (-not [string]::IsNullOrWhiteSpace($voiceChannelId)) { $voiceChannelId } else { $voiceChannelName }
                $checks.Add((New-Check -Name "voice_channel_access" -Status "fail" -Message "Bot cannot see configured voice channel '$target' in guild '$guildId'.")) | Out-Null
            } else {
                $checks.Add((New-Check -Name "voice_channel_access" -Status "warn" -Message "Voice channel access skipped because no voice target is configured.")) | Out-Null
            }
        } else {
            $code = if ($null -eq $channels.code) { "n/a" } else { [string]$channels.code }
            $checks.Add((New-Check -Name "voice_channel_access" -Status "fail" -Message "Could not list guild channels for voice validation (HTTP $code).")) | Out-Null
        }
    }

    if (-not [string]::IsNullOrWhiteSpace($channelId)) {
        $channel = Invoke-DiscordGet -Path "/channels/$channelId" -Token $token -Timeout $TimeoutSec
        if ($channel.ok) {
            $checks.Add((New-Check -Name "channel_access" -Status "pass" -Message "Bot can access channel id '$channelId'.")) | Out-Null
        } else {
            $code = if ($null -eq $channel.code) { "n/a" } else { [string]$channel.code }
            $checks.Add((New-Check -Name "channel_access" -Status "fail" -Message "Channel access failed for id '$channelId' (HTTP $code).")) | Out-Null
        }
    }
}

$passCount = @($checks | Where-Object { $_.status -eq "pass" }).Count
$warnCount = @($checks | Where-Object { $_.status -eq "warn" }).Count
$failCount = @($checks | Where-Object { $_.status -eq "fail" }).Count

$result = [ordered]@{
    generatedAt = (Get-Date).ToString("o")
    checks = $checks
    summary = [ordered]@{
        pass = $passCount
        warn = $warnCount
        fail = $failCount
    }
    nextAction = if ($failCount -gt 0) {
        "P0 blocked: fix token/guild/channel/voice dependency failures, then rerun this script before starting the bot runtime or adding Lantern to Lounge."
    } else {
        "Health checks passed. Safe to run Start-DiscordLoungeBot.ps1; voice join still requires LANTERN_DISCORD_ENABLE_VOICE=true."
    }
}

if ($Json) {
    $result | ConvertTo-Json -Depth 6
} else {
    Write-Output "Discord Bot Health Check"
    Write-Output "Pass: $passCount | Warn: $warnCount | Fail: $failCount"
    foreach ($check in $checks) {
        Write-Output ("[{0}] {1} - {2}" -f $check.status.ToUpper(), $check.name, $check.message)
    }
}

if ($failCount -gt 0) {
    exit 1
}

exit 0
