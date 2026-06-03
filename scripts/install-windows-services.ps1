#!/usr/bin/env pwsh
# Install Lantern OS Rust binaries as Windows Services (no Docker required)
# Usage: .\scripts\install-windows-services.ps1
# Requires: nssm.exe in PATH (download from https://nssm.cc/)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$DataDir = "$ProjectRoot\data"
$AssetsDir = "$ProjectRoot\assets"
$CsfBin = "$ProjectRoot\src\csf_rust\target\release\csf.exe"
$CaddBin = "$ProjectRoot\src\cadd_rust\target\release\cadd.exe"

Write-Host "=== Lantern OS Windows Service Installer ===" -ForegroundColor Cyan

# Check nssm
if (-not (Get-Command nssm -ErrorAction SilentlyContinue)) {
    Write-Error "nssm not found. Download from https://nssm.cc/ and add to PATH."
    exit 1
}

# Check binaries exist
if (-not (Test-Path $CsfBin)) {
    Write-Error "CSF binary not found at $CsfBin. Run 'cargo build --release' in src\csf_rust first."
    exit 1
}
if (-not (Test-Path $CaddBin)) {
    Write-Error "CADD binary not found at $CaddBin. Run 'cargo build --release' in src\cadd_rust first."
    exit 1
}

# Create data directories
@($DataDir, "$DataDir\archives", "$DataDir\logs", $AssetsDir, "$AssetsDir\brand", "$AssetsDir\incoming") | ForEach-Object {
    if (-not (Test-Path $_)) {
        New-Item -ItemType Directory -Path $_ -Force | Out-Null
        Write-Host "Created: $_"
    }
}

# Install LanternCSF service
Write-Host "`nInstalling LanternCSF service..." -ForegroundColor Yellow
nssm install LanternCSF $CsfBin | Out-Null
nssm set LanternCSF AppParameters "server --bind 0.0.0.0:9000 --data-dir `"$DataDir\archives`"" | Out-Null
nssm set LanternCSF DisplayName "Lantern OS CSF Worker" | Out-Null
nssm set LanternCSF Description "Headless CSF compression worker" | Out-Null
nssm set LanternCSF Start SERVICE_AUTO_START | Out-Null
nssm set LanternCSF AppDirectory $ProjectRoot | Out-Null
nssm set LanternCSF AppStdout "$DataDir\logs\csf.log" | Out-Null
nssm set LanternCSF AppStderr "$DataDir\logs\csf.log" | Out-Null
Write-Host "  LanternCSF installed" -ForegroundColor Green

# Install LanternCADD service
Write-Host "`nInstalling LanternCADD service..." -ForegroundColor Yellow
nssm install LanternCADD $CaddBin | Out-Null
nssm set LanternCADD AppParameters "watch `"$AssetsDir\incoming`" --brand-dir `"$AssetsDir\brand`"" | Out-Null
nssm set LanternCADD DisplayName "Lantern OS CADD Worker" | Out-Null
nssm set LanternCADD Description "Headless CADD validation worker" | Out-Null
nssm set LanternCADD Start SERVICE_AUTO_START | Out-Null
nssm set LanternCADD AppDirectory $ProjectRoot | Out-Null
nssm set LanternCADD AppStdout "$DataDir\logs\cadd.log" | Out-Null
nssm set LanternCADD AppStderr "$DataDir\logs\cadd.log" | Out-Null
Write-Host "  LanternCADD installed" -ForegroundColor Green

# Start services
Write-Host "`nStarting services..." -ForegroundColor Yellow
Start-Service LanternCSF -ErrorAction SilentlyContinue
Start-Service LanternCADD -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Check status
Write-Host "`n=== Service Status ===" -ForegroundColor Cyan
Get-Service LanternCSF, LanternCADD | Format-Table Name, Status, StartType

Write-Host "`n=== Endpoints ===" -ForegroundColor Green
Write-Host "  CSF:  http://localhost:9000"
Write-Host "  Logs: $DataDir\logs\"

Write-Host "`n=== Management ===" -ForegroundColor Green
Write-Host "  Stop:    net stop LanternCSF"
Write-Host "  Start:   net start LanternCSF"
Write-Host "  Remove:  nssm remove LanternCSF confirm"
Write-Host "  Restart: .\scripts\restart-headless.ps1"

Write-Host "`nDone. Services auto-start on boot. No Docker required." -ForegroundColor Cyan
