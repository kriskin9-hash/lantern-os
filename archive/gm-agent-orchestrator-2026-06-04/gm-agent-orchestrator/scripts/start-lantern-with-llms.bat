@echo off
REM Start Local LLMs and Lantern Desktop
REM This batch file launches both services in sequence

setlocal enabledelayedexpansion

echo.
echo ===============================================================
echo        Lantern + Local LLMs Startup Script
echo ===============================================================
echo.

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0

REM Start LM Studio + Ollama in PowerShell (non-blocking)
echo [*] Starting local LLM services (LM Studio + Ollama)...
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%start-local-llms.ps1"

REM Wait 5 seconds for services to start
echo.
echo [*] Waiting for services to initialize (5 seconds)...
timeout /t 5 /nobreak

REM Start Lantern Desktop
echo.
echo [*] Starting Lantern Desktop...
cd /d "%SCRIPT_DIR%.."
python scripts\lantern-desktop-auth-ui.py

echo.
echo [OK] Lantern session ended. Local LLMs still running.
echo.
pause
