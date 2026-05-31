# Lantern OS Setup Wizard for Courtney
# Interactive setup script for installing Lantern OS

param(
    [switch]$SkipPrereqCheck
)

$ErrorActionPreference = "Stop"

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Test-Prerequisite {
    param(
        [string]$Name,
        [string]$Command,
        [string]$MinVersion = $null
    )
    
    Write-ColorOutput "Checking $Name..." -ForegroundColor Cyan
    
    try {
        $result = & $Command 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "  ✓ $Name installed" -ForegroundColor Green
            return $true
        } else {
            Write-ColorOutput "  ✗ $Name not found" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-ColorOutput "  ✗ $Name not found" -ForegroundColor Red
        return $false
    }
}

function Show-Welcome {
    Clear-Host
    Write-ColorOutput "========================================" -ForegroundColor Cyan
    Write-ColorOutput "  Lantern OS Setup for Courtney" -ForegroundColor Cyan
    Write-ColorOutput "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-ColorOutput "This wizard will help you install Lantern OS on your computer." -ForegroundColor White
    Write-Host ""
    Write-ColorOutput "What will be installed:" -ForegroundColor Yellow
    Write-Host "  - Lantern OS repository"
    Write-Host "  - Desktop shortcut"
    Write-Host "  - Local-cloud bridge configuration"
    Write-Host ""
    Write-ColorOutput "Prerequisites:" -ForegroundColor Yellow
    Write-Host "  - Node.js 20+"
    Write-Host "  - Python 3+"
    Write-Host "  - Git"
    Write-Host "  - PowerShell (included with Windows)"
    Write-Host ""
}

function Check-Prerequisites {
    Write-ColorOutput "Checking prerequisites..." -ForegroundColor Cyan
    Write-Host ""
    
    $nodejs = Test-Prerequisite "Node.js" "node" "--version"
    $python = Test-Prerequisite "Python" "python" "--version"
    $git = Test-Prerequisite "Git" "git" "--version"
    $powershell = $true # PowerShell is always available
    
    Write-Host ""
    
    if (-not $nodejs -or -not $python -or -not $git) {
        Write-ColorOutput "Some prerequisites are missing!" -ForegroundColor Red
        Write-Host ""
        Write-ColorOutput "Please install:" -ForegroundColor Yellow
        if (-not $nodejs) {
            Write-Host "  - Node.js from https://nodejs.org (LTS version)"
        }
        if (-not $python) {
            Write-Host "  - Python from https://python.org/downloads/ (check 'Add Python to PATH')"
        }
        if (-not $git) {
            Write-Host "  - Git from https://git-scm.com/download/win"
        }
        Write-Host ""
        $continue = Read-Host "Continue anyway? (y/N)"
        if ($continue -ne "y" -and $continue -ne "Y") {
            exit 1
        }
    } else {
        Write-ColorOutput "All prerequisites installed!" -ForegroundColor Green
    }
    Write-Host ""
}

function Install-LanternOS {
    Write-ColorOutput "Installing Lantern OS..." -ForegroundColor Cyan
    Write-Host ""
    
    $installDir = "$env:USERPROFILE\Lantern-OS"
    
    # Check if already installed
    if (Test-Path $installDir) {
        Write-ColorOutput "Lantern OS already installed at: $installDir" -ForegroundColor Yellow
        $overwrite = Read-Host "Reinstall? (y/N)"
        if ($overwrite -ne "y" -and $overwrite -ne "Y") {
            return
        }
        Remove-Item -Path $installDir -Recurse -Force
    }
    
    # Clone repository
    Write-ColorOutput "Cloning Lantern OS repository..." -ForegroundColor Cyan
    try {
        git clone https://github.com/alex-place/lantern-os.git $installDir
        Write-ColorOutput "Repository cloned successfully!" -ForegroundColor Green
    } catch {
        Write-ColorOutput "Failed to clone repository" -ForegroundColor Red
        Write-ColorOutput "Please check your internet connection and try again" -ForegroundColor Yellow
        exit 1
    }

    # Install Node dependencies
    $appDir = Join-Path $installDir "apps\lantern-garage"
    if (Test-Path $appDir) {
        Write-ColorOutput "Installing Node.js dependencies..." -ForegroundColor Cyan
        Push-Location $appDir
        try {
            npm install --loglevel=error
            Write-ColorOutput "Dependencies installed!" -ForegroundColor Green
        } catch {
            Write-ColorOutput "npm install failed - Lantern may not start correctly." -ForegroundColor Yellow
        } finally {
            Pop-Location
        }
    }

    Write-Host ""
}

function Create-DesktopShortcut {
    Write-ColorOutput "Creating desktop shortcut..." -ForegroundColor Cyan
    
    $WshShell = New-Object -ComObject WScript.Shell
    $desktop = [Environment]::GetFolderPath("Desktop")
    $shortcutPath = Join-Path $desktop "Lantern OS.lnk"
    $installDir = "$env:USERPROFILE\Lantern-OS"
    
    $shortcut = $WshShell.CreateShortcut($shortcutPath)
    $shortcut.TargetPath = "powershell.exe"
    $shortcut.Arguments = "-ExecutionPolicy Bypass -File `"$installDir\scripts\Start-LanternGarageApp.ps1`""
    $shortcut.WorkingDirectory = $installDir
    $shortcut.Description = "Lantern OS"
    $shortcut.Save()
    
    Write-ColorOutput "Desktop shortcut created!" -ForegroundColor Green
    Write-Host ""
}

function Show-Completion {
    Clear-Host
    Write-ColorOutput "========================================" -ForegroundColor Cyan
    Write-ColorOutput "  Installation Complete!" -ForegroundColor Green
    Write-ColorOutput "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-ColorOutput "Lantern OS has been installed successfully!" -ForegroundColor White
    Write-Host ""
    Write-ColorOutput "To start Lantern OS:" -ForegroundColor Yellow
    Write-Host "  - Double-click the 'Lantern OS' desktop shortcut"
    Write-Host "  - Or run: powershell -ExecutionPolicy Bypass -File $env:USERPROFILE\Lantern-OS\scripts\Start-LanternGarageApp.ps1"
    Write-Host ""
    Write-ColorOutput "Local app will run at:" -ForegroundColor Yellow
    Write-Host "  http://127.0.0.1:4177"
    Write-Host ""
    Write-ColorOutput "For help or issues, see:" -ForegroundColor Yellow
    Write-Host "  - COURTNEY-DESKTOP-BRIDGE-SETUP-2026-05-30.md"
    Write-Host "  - COURTNEY-QUICK-SYNC-2026-05-30.md"
    Write-Host ""
    Read-Host "Press Enter to exit"
}

# Main execution
Show-Welcome

if (-not $SkipPrereqCheck) {
    Check-Prerequisites
}

Install-LanternOS
Create-DesktopShortcut
Show-Completion