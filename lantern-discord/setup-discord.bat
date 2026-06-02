@echo off
REM Discord Bot Environment Setup Batch Wrapper
REM Double-click this file to set up Discord bot environment variables

setlocal enabledelayedexpansion

echo.
echo ================================================================
echo Discord Bot Environment Setup
echo ================================================================
echo.

REM Get token from user
set /p TOKEN="Paste Discord Bot Token: "

if "!TOKEN!"=="" (
    echo Error: Token cannot be empty
    pause
    exit /b 1
)

REM Run PowerShell script
set "PS_BIN=pwsh"
where /q "%PS_BIN%"
if errorlevel 1 set "PS_BIN=powershell"
"%PS_BIN%" -NoProfile -ExecutionPolicy Bypass -File "%~dp0Set-DiscordEnvVars.ps1" -Token "!TOKEN!" -Permanent

echo.
echo ================================================================
echo Setup complete. You can close this window.
echo ================================================================
pause
