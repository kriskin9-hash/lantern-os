# Build Self-Extracting EXE Installer
# Creates a self-extracting EXE using PowerShell and .NET (no external tools required)

param(
    [string]$OutputDir = (Join-Path $PSScriptRoot "..\artifacts")
)

$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
$packageName = "Lantern-OS-Courtney-Setup"
$exePath = Join-Path $OutputDir "$packageName.exe"

Write-Host "Building self-extracting EXE installer..." -ForegroundColor Cyan

# Create temporary directory for packaging
$tempDir = Join-Path $env:TEMP "lantern-exe-build"
if (Test-Path $tempDir) {
    Remove-Item -Path $tempDir -Recurse -Force
}
New-Item -ItemType Directory -Path $tempDir -Force | Out-Null

# Copy files to package
Copy-Item (Join-Path $root "scripts\Invoke-CourtneySetupWizard.ps1") -Destination $tempDir
Copy-Item (Join-Path $root "docs\COURTNEY-QUICK-SYNC-2026-05-30.md") -Destination $tempDir
Copy-Item (Join-Path $root "docs\COURTNEY-DESKTOP-BRIDGE-SETUP-2026-05-30.md") -Destination $tempDir

# Create launcher script
$launcherScript = @"
# Lantern OS Setup Launcher
# Self-extracting installer

`$scriptPath = `$PSScriptRoot
`$setupScript = Join-Path `$scriptPath "Invoke-CourtneySetupWizard.ps1"

Write-Host "Lantern OS Setup for Courtney" -ForegroundColor Cyan
Write-Host "=============================" -ForegroundColor Cyan
Write-Host ""

if (Test-Path `$setupScript) {
    Write-Host "Starting setup wizard..." -ForegroundColor Green
    & `$setupScript
} else {
    Write-Host "Error: Setup script not found" -ForegroundColor Red
    Read-Host "Press Enter to exit"
}
"@

$launcherScript | Set-Content (Join-Path $tempDir "Setup-Lantern.ps1") -Encoding UTF8

# Create a simple self-extracting EXE using PowerShell IExpress (built into Windows)
$issContent = @"
[Version]
Class=IEXPRESS
SEDVersion=3
[Options]
PackagePurpose=InstallApp
ShowInstallProgramWindow=1
HideExtractAnimation=1
UseLongFileName=1
InsideCompressed=0
CAB_FixedSize=0
CAB_ResvCodeSigning=0
RebootMode=N
InstallPrompt=
DisplayLicense=
FinishMessage=
TargetName=$exePath
FriendlyName=Lantern OS Setup
AppLaunched=cmd /c PowerShell -ExecutionPolicy Bypass -File "Setup-Lantern.ps1"
PostInstallCmd=<None>
AdminRightsStub=1
[Strings]
SourceFiles=SourceFiles
[SourceFiles]
SourceFiles0=$tempDir\
[SourceFiles0]
"@

# Add files to IExpress configuration
$files = Get-ChildItem $tempDir -File
foreach ($file in $files) {
    $issContent += "`"$($file.Name)`"=`"$($file.FullName)`"`n"
}

$issPath = Join-Path $tempDir "setup.iss"
$issContent | Set-Content $issPath -Encoding ASCII

# Ensure output directory exists
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

# Build using IExpress
Write-Host "Building EXE with IExpress..." -ForegroundColor Cyan
$iexpressPath = Join-Path $env:SystemRoot "System32\iexpress.exe"

if (Test-Path $iexpressPath) {
    & $iexpressPath /Q /N $issPath
    
    if (Test-Path $exePath) {
        Write-Host "EXE installer created successfully!" -ForegroundColor Green
        Write-Host "Location: $exePath" -ForegroundColor Gray
        Write-Host "Size: $((Get-Item $exePath).Length / 1KB) KB" -ForegroundColor Gray
    } else {
        Write-Host "IExpress failed to create EXE" -ForegroundColor Red
    }
} else {
    Write-Host "IExpress not found. Creating batch file launcher instead..." -ForegroundColor Yellow
    
    # Fallback: Create a batch file that extracts and runs
    $batchContent = @"
@echo off
setlocal
set SCRIPT_DIR=%~dp0
powershell -ExecutionPolicy Bypass -File "%SCRIPT_DIR%Setup-Lantern.ps1"
"@
    
    $batPath = Join-Path $OutputDir "$packageName.bat"
    $batchContent | Set-Content $batPath -Encoding ASCII
    
    # Also create a ZIP as fallback
    $zipPath = Join-Path $OutputDir "$packageName.zip"
    Compress-Archive -Path "$tempDir\*" -DestinationPath $zipPath -Force
    
    Write-Host "Created batch launcher: $batPath" -ForegroundColor Green
    Write-Host "Created ZIP archive: $zipPath" -ForegroundColor Green
}

# Cleanup
Remove-Item -Path $tempDir -Recurse -Force

Write-Host "Build complete!" -ForegroundColor Green
