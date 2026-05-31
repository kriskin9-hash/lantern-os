# Build Courtney EXE Installer
# Uses Inno Setup to create a Windows EXE installer

param(
    [string]$InnoSetupPath = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
)

$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
$issScript = Join-Path $PSScriptRoot "lantern-os-courtney-setup.iss"
$outputDir = Join-Path $root "artifacts"

Write-Host "Building Courtney EXE installer..." -ForegroundColor Cyan

# Check if Inno Setup is installed
if (-not (Test-Path $InnoSetupPath)) {
    Write-Host "Inno Setup not found at: $InnoSetupPath" -ForegroundColor Yellow
    Write-Host "Please install Inno Setup from: https://jrsoftware.org/isdl.php" -ForegroundColor Yellow
    Write-Host "Or specify the path using -InnoSetupPath parameter" -ForegroundColor Yellow
    exit 1
}

# Ensure output directory exists
if (-not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
}

# Build the installer
Write-Host "Running Inno Setup compiler..." -ForegroundColor Cyan
& $InnoSetupPath $issScript "/O$outputDir"

if ($LASTEXITCODE -eq 0) {
    Write-Host "EXE installer created successfully!" -ForegroundColor Green
    $exePath = Join-Path $outputDir "Lantern-OS-Courtney-Setup.exe"
    if (Test-Path $exePath) {
        Write-Host "Location: $exePath" -ForegroundColor Gray
        Write-Host "Size: $((Get-Item $exePath).Length / 1MB) MB" -ForegroundColor Gray
    }
} else {
    Write-Host "Failed to build EXE installer" -ForegroundColor Red
    exit 1
}
