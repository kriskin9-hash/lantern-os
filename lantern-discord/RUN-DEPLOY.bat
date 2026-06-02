@echo off
REM Discord Bot Deployment Wrapper
REM Double-click to deploy Discord bot to online status

cls
echo.
echo ================================================================
echo LANTERN DISCORD BOT - AUTO-DEPLOYMENT
echo ================================================================
echo.
echo Starting deployment script...
echo.

cd /d "%~dp0"
set "PS_BIN=pwsh"
where /q "%PS_BIN%"
if errorlevel 1 set "PS_BIN=powershell"
"%PS_BIN%" -NoProfile -ExecutionPolicy Bypass -File deploy-discord-bot.ps1

echo.
echo ================================================================
echo Deployment finished. Press any key to close.
echo ================================================================
pause
