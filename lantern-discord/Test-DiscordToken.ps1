<#
.SYNOPSIS
Quick Discord bot token validation via CLI.

.PARAMETER Token
Discord bot token.

.PARAMETER GuildId
Optional guild ID to test.

.PARAMETER ChannelId
Optional channel ID to test.

.PARAMETER Quiet
Suppress detailed success output.
#>

param(
    [Parameter(Mandatory = $true)][string]$Token,
    [string]$GuildId,
    [string]$ChannelId,
    [switch]$ShowPermissions,
    [switch]$Quiet
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$DiscordApiBase = "https://discordapp.com/api/v10"
$headers = @{
    Authorization = "Bot $Token"
    "Content-Type" = "application/json"
}

function Invoke-DiscordApi {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [ValidateSet("Get", "Post", "Delete")][string]$Method = "Get",
        [string]$Body
    )

    $invokeArgs = @{
        Uri = "$DiscordApiBase/$Path"
        Method = $Method
        Headers = $headers
        TimeoutSec = 10
    }

    if ($Body) {
        $invokeArgs["Body"] = $Body
    }

    Invoke-RestMethod @invokeArgs
}

Write-Host ""
Write-Host "Discord Bot Token Validator" -ForegroundColor Cyan
Write-Host ("=" * 50) -ForegroundColor Cyan

Write-Host "Testing Discord token..." -ForegroundColor Cyan
try {
    $bot = Invoke-DiscordApi -Path "users/@me"
    if (-not $Quiet) {
        Write-Host "[OK] Token valid" -ForegroundColor Green
        Write-Host "  Bot: $($bot.username)#$($bot.discriminator)" -ForegroundColor Gray
        Write-Host "  ID: $($bot.id)" -ForegroundColor Gray
    }
}
catch {
    Write-Host "[ERROR] Token invalid: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

if ($GuildId) {
    Write-Host ""
    Write-Host "Testing guild access..." -ForegroundColor Cyan
    try {
        $guild = Invoke-DiscordApi -Path "guilds/$GuildId"
        if (-not $Quiet) {
            Write-Host "[OK] Guild accessible" -ForegroundColor Green
            Write-Host "  Guild: $($guild.name)" -ForegroundColor Gray
            Write-Host "  ID: $($guild.id)" -ForegroundColor Gray
        }
    }
    catch {
        Write-Host "[ERROR] Guild not accessible: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}

if ($ChannelId) {
    Write-Host ""
    Write-Host "Testing channel access..." -ForegroundColor Cyan
    try {
        $channel = Invoke-DiscordApi -Path "channels/$ChannelId"
        if (-not $Quiet) {
            Write-Host "[OK] Channel accessible" -ForegroundColor Green
            Write-Host "  Channel: #$($channel.name)" -ForegroundColor Gray
            Write-Host "  ID: $($channel.id)" -ForegroundColor Gray
            Write-Host "  Type: $($channel.type)" -ForegroundColor Gray
        }
    }
    catch {
        Write-Host "[ERROR] Channel not accessible: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }

    Write-Host ""
    Write-Host "Testing send permissions..." -ForegroundColor Cyan
    $body = @{ content = "Lantern Lounge Bot Health Check: $(Get-Date -Format 'u')" } | ConvertTo-Json

    try {
        $message = Invoke-DiscordApi -Path "channels/$ChannelId/messages" -Method Post -Body $body
        if (-not $Quiet) {
            Write-Host "[OK] Message sent successfully" -ForegroundColor Green
            Write-Host "  Message ID: $($message.id)" -ForegroundColor Gray
        }

        Invoke-DiscordApi -Path "channels/$ChannelId/messages/$($message.id)" -Method Delete | Out-Null
    }
    catch {
        Write-Host "[ERROR] Cannot send message: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}

if ($ShowPermissions) {
    Write-Host ""
    Write-Host "ShowPermissions was requested, but this simplified validator does not decode permission bits." -ForegroundColor Yellow
}

Write-Host ""
Write-Host ("=" * 50) -ForegroundColor Cyan
Write-Host "[OK] Validation complete" -ForegroundColor Green
Write-Host ""
