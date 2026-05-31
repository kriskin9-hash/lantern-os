<#
.SYNOPSIS
    Builds Lantern-OS-Courtney-Setup.exe using ps2exe (no Inno Setup required).
    Run this script ONCE on Alex's machine to produce the exe.
    The exe can then be given directly to Courtney.

.NOTES
    ps2exe is installed from PSGallery on first run (no admin required).
    Output: artifacts\Lantern-OS-Courtney-Setup.exe
#>

param(
    [switch]$SkipModuleInstall
)

$ErrorActionPreference = "Stop"

$root     = Resolve-Path (Join-Path $PSScriptRoot "..")
$srcPs1   = Join-Path $PSScriptRoot "Invoke-CourtneySetupWizard.ps1"
$outDir   = Join-Path $root "artifacts"
$outExe   = Join-Path $outDir "Lantern-OS-Courtney-Setup.exe"

if (-not (Test-Path $outDir)) {
    New-Item -ItemType Directory -Path $outDir -Force | Out-Null
}

# Install ps2exe if not already available
if (-not $SkipModuleInstall) {
    if (-not (Get-Module -ListAvailable -Name ps2exe)) {
        Write-Host "Installing ps2exe from PSGallery (user scope, no admin needed)..." -ForegroundColor Cyan
        Install-Module -Name ps2exe -Scope CurrentUser -Force -AllowClobber
    }
}

Import-Module ps2exe -ErrorAction Stop

Write-Host "Compiling $srcPs1 -> $outExe" -ForegroundColor Cyan

Invoke-ps2exe `
    -InputFile  $srcPs1 `
    -OutputFile $outExe `
    -NoConsole:$false `
    -Title      "Lantern OS Setup for Courtney" `
    -Description "Installs Lantern OS on Courtney's Windows laptop" `
    -Company    "Lantern OS" `
    -Version    "1.0.0" `
    -requireAdmin:$false

if (Test-Path $outExe) {
    $sizeMb = [math]::Round((Get-Item $outExe).Length / 1MB, 2)
    Write-Host ""
    Write-Host "EXE built successfully!" -ForegroundColor Green
    Write-Host "  Path : $outExe" -ForegroundColor Gray
    Write-Host "  Size : $sizeMb MB" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Give Courtney: artifacts\Lantern-OS-Courtney-Setup.exe" -ForegroundColor Yellow
    Write-Host "She double-clicks it and follows the wizard." -ForegroundColor Yellow
} else {
    Write-Host "Build failed - exe not found at expected path." -ForegroundColor Red
    exit 1
}
