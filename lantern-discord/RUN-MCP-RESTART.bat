@echo off
REM Restart Lantern OS MCP Server

cd /d "%~dp0"
echo.
echo ================================================================
echo LANTERN OS - RESTART MCP SERVER
echo ================================================================
echo.

REM Try to detect PowerShell version
set "PS_BIN=pwsh"
where /q "%PS_BIN%"
if errorlevel 1 set "PS_BIN=powershell"

REM Run the restart script (will request elevation if needed)
"%PS_BIN%" -NoProfile -ExecutionPolicy Bypass -File restart-mcp-and-deploy.ps1

echo.
echo Press any key to close.
pause
