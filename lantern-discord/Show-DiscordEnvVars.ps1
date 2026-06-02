<#
.SYNOPSIS
Display Discord environment variables for validation.

.DESCRIPTION
Reads and displays all Discord-related env vars currently set.
Safe to run — doesn't modify anything, just displays values.
#>

Write-Host "`nDiscord Environment Variables:" -ForegroundColor Cyan
Write-Host $("=" * 70) -ForegroundColor Cyan

$vars = @(
    "DISCORD_BOT_TOKEN",
    "LANTERN_DISCORD_GUILD_ID",
    "LANTERN_DISCORD_GUILD_NAME",
    "LANTERN_DISCORD_CHANNEL_ID",
    "LANTERN_DISCORD_CHANNEL_NAME",
    "LANTERN_VOICE_CHANNEL_ID",
    "LANTERN_VOICE_CHANNEL_NAME",
    "LANTERN_STATUS_URL",
    "LANTERN_DISCORD_ENABLE_VOICE",
    "LANTERN_DISCORD_ENABLE_RADIO",
    "LANTERN_RADIO_URL"
)

$found = 0
$missing = 0

foreach ($var in $vars) {
    $value = Get-Item -Path "env:$var" -ErrorAction SilentlyContinue
    if ($value) {
        $displayValue = if ($var -like "*TOKEN*") {
            $v = $value.Value
            if ($v.Length -gt 20) { "$($v.Substring(0,10))...$(($v | Measure-Object -Character).Characters - 10 | % { '.' * $_ })" }
            else { "***REDACTED***" }
        } else {
            $value.Value
        }
        Write-Host "$var = $displayValue" -ForegroundColor Green
        $found++
    } else {
        Write-Host "$var = [NOT SET]" -ForegroundColor Yellow
        $missing++
    }
}

Write-Host $("=" * 70) -ForegroundColor Cyan
Write-Host "Summary: $found set, $missing missing" -ForegroundColor Cyan

# Show which are REQUIRED
Write-Host "`nRequired variables (must have):" -ForegroundColor Red
Write-Host "  - DISCORD_BOT_TOKEN" -ForegroundColor Red
Write-Host "  - LANTERN_DISCORD_GUILD_ID" -ForegroundColor Red
Write-Host "  - LANTERN_DISCORD_CHANNEL_ID" -ForegroundColor Red
Write-Host "  - LANTERN_VOICE_CHANNEL_ID" -ForegroundColor Red

Write-Host ""
