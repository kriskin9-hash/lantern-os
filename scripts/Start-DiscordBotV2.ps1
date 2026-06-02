# Start-DiscordBotV2.ps1
# Lantern OS Discord Bot v2 Launcher
# Generated: 2026-05-31

param(
    [switch]$NoHealthCheck = $false,
    [switch]$SkipOllama = $false
)

$ErrorActionPreference = "Stop"
$repoRoot = Resolve-Path "$PSScriptRoot\.."
$botPath = "$repoRoot\src\discord_lounge_bot\bot_v2.py"
$venvPath = "$repoRoot\.venv"

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "Lantern OS Discord Bot v2" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

# Check Python
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Host "[FATAL] Python not found on PATH" -ForegroundColor Red
    exit 1
}
Write-Host "[+] Python: $(python --version)"

# Check virtual environment
if (Test-Path "$venvPath\Scripts\python.exe") {
    $pythonExe = "$venvPath\Scripts\python.exe"
    Write-Host "[+] Using virtual environment"
} else {
    $pythonExe = "python"
    Write-Host "[!] No virtual environment found, using system Python"
}

# Install dependencies
Write-Host ""
Write-Host "[*] Checking dependencies..." -ForegroundColor Yellow
& $pythonExe -c "import discord" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "[!] Installing discord.py..."
    & $pythonExe -m pip install -r "$repoRoot\src\discord_lounge_bot\requirements_v2.txt" --quiet
}
Write-Host "[+] discord.py ready"

# Check environment variables
Write-Host ""
Write-Host "[*] Checking environment..." -ForegroundColor Yellow
$required = @("DISCORD_BOT_TOKEN", "LANTERN_DISCORD_GUILD_ID")
$missing = @()
foreach ($var in $required) {
    if (-not [Environment]::GetEnvironmentVariable($var)) {
        $missing += $var
    }
}
if ($missing) {
    Write-Host "[FATAL] Missing environment variables: $($missing -join ', ')" -ForegroundColor Red
    Write-Host "Set them before running the bot:"
    Write-Host "  `$env:DISCORD_BOT_TOKEN = 'your_token_here'"
    Write-Host "  `$env:LANTERN_DISCORD_GUILD_ID = 'your_guild_id_here'"
    exit 1
}
Write-Host "[+] Environment variables set"

# Health check
if (-not $NoHealthCheck) {
    Write-Host ""
    Write-Host "[*] Running health check..." -ForegroundColor Yellow
    & $pythonExe -c "import discord; print('discord.py version:', discord.__version__)"
    Write-Host "[+] Health check passed"
}

# Start bot
Write-Host ""
Write-Host "[*] Starting Lantern OS Discord Bot v2..." -ForegroundColor Yellow
Write-Host "[+] Slash commands + role gating + notebook integration"
Write-Host "[+] Stop with Ctrl+C"
Write-Host ""

& $pythonExe $botPath
