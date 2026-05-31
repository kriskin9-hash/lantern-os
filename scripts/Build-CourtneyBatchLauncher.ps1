# Build Courtney Batch Launcher
# Creates a simple batch file launcher for Courtney to run the setup

param(
    [string]$OutputDir = (Join-Path $PSScriptRoot "..\artifacts")
)

$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
$packageName = "Lantern-OS-Courtney-Setup"
$batPath = Join-Path $OutputDir "$packageName.bat"

Write-Host "Building Courtney batch launcher..." -ForegroundColor Cyan

# Create batch file content
$batchContent = @"
@echo off
REM Lantern OS Setup Launcher for Courtney
REM Double-click this file to start the Lantern OS setup

echo.
echo ========================================
echo   Lantern OS Setup for Courtney
echo ========================================
echo.

REM Check if PowerShell is available
where powershell >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: PowerShell not found
    echo Please install PowerShell or contact support
    pause
    exit /b 1
)

REM Run the setup wizard
powershell -ExecutionPolicy Bypass -File "%~dp0Invoke-CourtneySetupWizard.ps1"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Setup encountered an error. Please check the documentation.
    pause
) else (
    echo.
    echo Setup completed successfully!
    echo You can now start Lantern OS from your desktop shortcut.
    timeout /t 5
)
"@

# Ensure output directory exists
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

# Write batch file
$batchContent | Set-Content $batPath -Encoding ASCII

# Copy setup files to output directory
Copy-Item (Join-Path $root "scripts\Invoke-CourtneySetupWizard.ps1") -Destination $OutputDir -Force
Copy-Item (Join-Path $root "docs\COURTNEY-QUICK-SYNC-2026-05-30.md") -Destination $OutputDir -Force
Copy-Item (Join-Path $root "docs\COURTNEY-DESKTOP-BRIDGE-SETUP-2026-05-30.md") -Destination $OutputDir -Force

# Create README for the package
$readmeContent = @"
# Lantern OS Setup for Courtney

**Date:** 2026-05-30
**Version:** 1.0.0

## Quick Start

1. **Double-click:** `Lantern-OS-Courtney-Setup.bat`
2. **Follow the prompts** in the setup wizard
3. **Start Lantern OS** using the desktop shortcut

## What This Installer Does

- Checks prerequisites (Node.js, Python, Git, PowerShell)
- Clones the Lantern OS repository
- Configures Git for your user
- Creates a desktop shortcut
- Sets up local-cloud bridge

## Prerequisites

Before running the installer, ensure you have:
- **Node.js 20+** - Download from https://nodejs.org (LTS version)
- **Python 3+** - Download from https://python.org/downloads/ (check "Add Python to PATH")
- **Git** - Download from https://git-scm.com/download/win
- **PowerShell** - Included with Windows (no installation needed)

## Manual Setup

If the wizard fails, see:
- `COURTNEY-DESKTOP-BRIDGE-SETUP-2026-05-30.md` - Full bridge setup guide
- `COURTNEY-QUICK-SYNC-2026-05-30.md` - Quick sync commands

## Support

If you encounter issues:
1. Check the troubleshooting section in the bridge setup guide
2. Contact the Lantern OS operator for help

## After Installation

- Local app runs at: http://127.0.0.1:4177
- Cloud chat available via Codex Cloud
- Discord bot in collaboration channel

---

**Prepared for:** Courtney Blasioli
**Date:** 2026-05-30
"@

$readmeContent | Set-Content (Join-Path $OutputDir "README.md") -Encoding UTF8

Write-Host "Batch launcher created successfully!" -ForegroundColor Green
Write-Host "Location: $batPath" -ForegroundColor Gray
Write-Host "Size: $((Get-Item $batPath).Length / 1KB) KB" -ForegroundColor Gray
Write-Host ""
Write-Host "Package contents:" -ForegroundColor Cyan
Write-Host "- Lantern-OS-Courtney-Setup.bat (launcher)" -ForegroundColor Gray
Write-Host "- Invoke-CourtneySetupWizard.ps1 (setup wizard)" -ForegroundColor Gray
Write-Host "- Documentation files" -ForegroundColor Gray
Write-Host "- README.md" -ForegroundColor Gray
