<#
.SYNOPSIS
    Run browser automation tests using Playwright.

.DESCRIPTION
    Executes Playwright browser tests for Lantern OS surfaces.
    Requires Node.js and Playwright to be installed.

.PARAMETER Headless
    Run tests in headless mode (default: true)

.PARAMETER Browser
    Browser to test with (chromium, firefox, webkit, all)

.EXAMPLE
    .\scripts\Test-BrowserAutomation.ps1 -Browser all
#>
[CmdletBinding()]
param(
    [switch]$Headless,
    [ValidateSet("chromium", "firefox", "webkit", "all")]
    [string]$Browser = "chromium"
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$testsDir = Join-Path $repoRoot "tests"

Write-Host "Running browser automation tests..." -ForegroundColor Cyan

# Check if Node.js is installed
$nodeVersion = node --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Node.js is not installed. Please install Node.js to run browser tests." -ForegroundColor Red
    exit 1
}
Write-Host "Node.js version: $nodeVersion" -ForegroundColor Green

# Check if Playwright is installed
Push-Location $testsDir
if (-not (Test-Path "node_modules")) {
    Write-Host "Installing Playwright dependencies..." -ForegroundColor Yellow
    npm ci
    npx playwright install --with-deps
}

# Run Playwright tests
$browserArg = if ($Browser -eq "all") { "" } else { "--project=$Browser" }
$headlessArg = if ($Headless) { "" } else { "--headed" }
# Default to headless if not specified
if (-not $Headless) {
    $headlessArg = ""
}

Write-Host "Starting browser tests (Browser: $Browser, Headless: $Headless)..." -ForegroundColor Cyan
npx playwright test $browserArg $headlessArg

$exitCode = $LASTEXITCODE

if ($exitCode -eq 0) {
    Write-Host "Browser tests passed" -ForegroundColor Green
} else {
    Write-Host "Browser tests failed with exit code: $exitCode" -ForegroundColor Red
    Write-Host "Run 'npx playwright show-report' to view detailed results" -ForegroundColor Yellow
}

Pop-Location
exit $exitCode
