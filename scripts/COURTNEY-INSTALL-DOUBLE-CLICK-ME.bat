@echo off
title Lantern OS Setup for Courtney
color 0B

echo ========================================
echo   Lantern OS Setup for Courtney
echo ========================================
echo.
echo This will install Lantern OS on your computer.
echo.

:: Check if running from inside an existing lantern-os repo
set "REPO_DIR=%~dp0.."
set "LAUNCH_PS1=%REPO_DIR%\scripts\Invoke-CourtneySetupWizard.ps1"

if exist "%LAUNCH_PS1%" (
    echo Found Lantern OS repo. Running setup wizard...
    echo.
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%LAUNCH_PS1%"
    goto :end
)

:: Not inside a repo - download and run the wizard directly from GitHub
echo Downloading Lantern OS setup wizard from GitHub...
echo.

set "TEMP_DIR=%TEMP%\LanternOSSetup"
if not exist "%TEMP_DIR%" mkdir "%TEMP_DIR%"

set "WIZARD_URL=https://raw.githubusercontent.com/alex-place/lantern-os/master/scripts/Invoke-CourtneySetupWizard.ps1"
set "WIZARD_PS1=%TEMP_DIR%\Invoke-CourtneySetupWizard.ps1"

powershell.exe -NoProfile -ExecutionPolicy Bypass -Command ^
    "try { Invoke-WebRequest -Uri '%WIZARD_URL%' -OutFile '%WIZARD_PS1%' -UseBasicParsing; Write-Host 'Download complete.' } catch { Write-Host 'Download failed. Check internet connection.'; exit 1 }"

if not exist "%WIZARD_PS1%" (
    echo.
    echo ERROR: Could not download setup wizard.
    echo Please check your internet connection and try again.
    echo Or ask Alex to copy the lantern-os folder directly.
    echo.
    pause
    exit /b 1
)

echo Running Lantern OS setup wizard...
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%WIZARD_PS1%"

:end
echo.
echo Setup finished. Press any key to close.
pause > nul
