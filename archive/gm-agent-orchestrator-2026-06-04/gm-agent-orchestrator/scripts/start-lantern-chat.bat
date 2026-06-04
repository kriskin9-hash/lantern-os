@echo off
REM Quick launcher for Lantern Chat (requires auth first)

setlocal enabledelayedexpansion

echo.
echo ===============================================================
echo        Lantern Chat Launcher
echo ===============================================================
echo.

cd /d "%~dp0.."

echo [*] Starting Lantern with Chat...
python scripts\lantern-desktop-auth-ui.py

echo.
echo [*] Chat session ended
echo.
pause
