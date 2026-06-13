# Lantern Lounge Bot — Windows launch script
# Streams Frank Sinatra radio + binaural beats from Internet Archive
#
# Prerequisites:
#   pip install "discord.py[voice]" PyNaCl
#   winget install Gyan.FFmpeg
#
# Set LOUNGE_BOT_TOKEN in .env (or falls back to DISCORD_BOT_TOKEN)

$repoRoot  = Split-Path $PSScriptRoot -Parent
$botScript = Join-Path $repoRoot "src\sinatra_lounge\bot.py"
$logFile   = Join-Path $repoRoot "data\discord\lounge.log"
$errFile   = Join-Path $repoRoot "data\discord\lounge.err.log"

# Ensure log dir exists
New-Item -ItemType Directory -Force -Path (Split-Path $logFile) | Out-Null

Write-Host "Starting Lantern Lounge Bot..."
Write-Host "  Bot script: $botScript"
Write-Host "  Log:        $logFile"
Write-Host ""

$proc = Start-Process python `
    -ArgumentList "-u", $botScript `
    -RedirectStandardOutput $logFile `
    -RedirectStandardError $errFile `
    -WorkingDirectory $repoRoot `
    -PassThru -WindowStyle Hidden

Write-Host "Started PID=$($proc.Id)"
Write-Host "Tail log:   Get-Content '$logFile' -Wait"
Write-Host "Stop:       Stop-Process -Id $($proc.Id)"
