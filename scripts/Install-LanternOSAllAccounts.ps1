<#
.SYNOPSIS
    Non-interactive installer. Installs Lantern OS for the current user and
    optionally syncs to other local Windows accounts.
    Safe to run multiple times - updates existing installs.

.EXAMPLE
    # Install/update for current user only
    powershell -ExecutionPolicy Bypass -File .\scripts\Install-LanternOSAllAccounts.ps1

    # Install/update and also copy to CodexSandboxOnline account
    powershell -ExecutionPolicy Bypass -File .\scripts\Install-LanternOSAllAccounts.ps1 -AllAccounts
#>
param(
    [switch]$AllAccounts,
    [string]$SourceRepo = ""   # Default: use the repo this script lives in
)

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Msg, [string]$Color = "Cyan")
    Write-Host ""
    Write-Host ">>> $Msg" -ForegroundColor $Color
}

function Install-ForUser {
    param(
        [string]$UserProfile,
        [string]$UserName,
        [string]$SourceDir
    )

    $installDir = Join-Path $UserProfile "Lantern-OS"
    $appDir     = Join-Path $installDir "apps\lantern-garage"
    $startScript = Join-Path $installDir "scripts\Start-LanternGarageApp.ps1"
    $desktop    = Join-Path $UserProfile "Desktop"

    Write-Step "Installing for user: $UserName -> $installDir"

    # Skip system/inaccessible profiles
    try { $null = [System.IO.Directory]::GetAccessControl($UserProfile) } catch {
        Write-Host "  Skipped (no access to $UserProfile)" -ForegroundColor Gray
        return
    }

    # Sync files (robocopy: mirror repo to installDir, skip .git and node_modules)
    Write-Host "  Syncing repo files..." -ForegroundColor Gray
    $robocopyArgs = @(
        $SourceDir, $installDir,
        "/MIR", "/XD", ".git", "node_modules", ".netlify",
        "/XF", "*.log", "*.lock",
        "/NFL", "/NDL", "/NJH", "/NJS", "/NC", "/NS"
    )
    robocopy @robocopyArgs | Out-Null
    # robocopy exit codes 0-7 are success
    if ($LASTEXITCODE -gt 7) {
        Write-Host "  WARNING: robocopy exit $LASTEXITCODE - some files may not have copied." -ForegroundColor Yellow
    } else {
        Write-Host "  Files synced OK." -ForegroundColor Green
    }

    # npm install
    if (Test-Path $appDir) {
        Write-Host "  Running npm install..." -ForegroundColor Gray
        Push-Location $appDir
        npm install --loglevel=error 2>&1 | Out-Null
        Pop-Location
        Write-Host "  npm install OK." -ForegroundColor Green
    }

    # Desktop shortcut (only works for current user's desktop)
    try {
        if ((Test-Path $desktop -ErrorAction Stop) -and (Test-Path $startScript)) {
            Write-Host "  Creating desktop shortcut..." -ForegroundColor Gray
            $wsh = New-Object -ComObject WScript.Shell
            $lnk = $wsh.CreateShortcut((Join-Path $desktop "Lantern OS.lnk"))
            $lnk.TargetPath    = "powershell.exe"
            $lnk.Arguments     = "-NoProfile -ExecutionPolicy Bypass -File `"$startScript`""
            $lnk.WorkingDirectory = $installDir
            $lnk.Description   = "Start Lantern OS at http://127.0.0.1:4177"
            $lnk.Save()
            Write-Host "  Shortcut created: $(Join-Path $desktop 'Lantern OS.lnk')" -ForegroundColor Green
        }
    } catch {
        Write-Host "  Shortcut skipped (no desktop access for $UserName)" -ForegroundColor Gray
    }

    # Quick smoke test - can node parse server.js?
    $serverJs = Join-Path $appDir "server.js"
    if (Test-Path $serverJs) {
        $check = node --check $serverJs 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  node syntax check: PASS" -ForegroundColor Green
        } else {
            Write-Host "  node syntax check: FAIL - $check" -ForegroundColor Red
        }
    }

    Write-Host ""
    Write-Host "  Done: $UserName install at $installDir" -ForegroundColor Green
    Write-Host "  Start : powershell -ExecutionPolicy Bypass -File `"$startScript`"" -ForegroundColor Yellow
    Write-Host "  URL   : http://127.0.0.1:4177" -ForegroundColor Yellow
}

# ---- Main ----

# Resolve source directory (repo root = two levels up from this script)
if (-not $SourceRepo) {
    $SourceRepo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Lantern OS All-Accounts Installer" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Source : $SourceRepo"
Write-Host "  Date   : $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
Write-Host ""

# Always install for current user
Install-ForUser -UserProfile $env:USERPROFILE -UserName $env:USERNAME -SourceDir $SourceRepo

# Optionally install for other local accounts
if ($AllAccounts) {
    $otherProfiles = Get-WmiObject Win32_UserProfile -ErrorAction SilentlyContinue |
        Where-Object { $_.Special -eq $false -and $_.LocalPath -ne $env:USERPROFILE } |
        Select-Object -ExpandProperty LocalPath

    foreach ($profilePath in $otherProfiles) {
        $uname = Split-Path $profilePath -Leaf
        if (Test-Path $profilePath) {
            Install-ForUser -UserProfile $profilePath -UserName $uname -SourceDir $SourceRepo
        }
    }
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  Installation Complete" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "To start Lantern OS (any account):" -ForegroundColor Yellow
Write-Host "  Double-click 'Lantern OS' shortcut on Desktop" -ForegroundColor White
Write-Host "  OR: powershell -ExecutionPolicy Bypass -File `"~\Lantern-OS\scripts\Start-LanternGarageApp.ps1`"" -ForegroundColor White
Write-Host ""
Write-Host "Browser opens to: http://127.0.0.1:4177" -ForegroundColor Cyan
Write-Host ""
