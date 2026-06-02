[CmdletBinding()]
param(
    [int]$Port = 3000,
    [string]$Headless = "true",
    [switch]$Wait
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = (Resolve-Path "$PSScriptRoot\..").Path
$apiDir = Join-Path $root "tools\gpt-web-api"

$headlessValue = $true
if (-not [string]::IsNullOrWhiteSpace($Headless)) {
    $normalized = $Headless.Trim().ToLowerInvariant()
    switch ($normalized) {
        "true" { $headlessValue = $true; break }
        "false" { $headlessValue = $false; break }
        "1" { $headlessValue = $true; break }
        "0" { $headlessValue = $false; break }
        "$true" { $headlessValue = $true; break }
        "$false" { $headlessValue = $false; break }
        default { $headlessValue = $true; break }
    }
}

Write-Host "=== GPT Web API Server ===" -ForegroundColor Cyan
Write-Host "Port: $Port"
Write-Host "Headless: $headlessValue"
Write-Host "Directory: $apiDir"
Write-Host ""

if (-not (Test-Path $apiDir)) {
    Write-Error "GPT Web API directory not found: $apiDir"
    exit 1
}

# Check if Node.js is installed
try {
    $nodeVersion = & node --version 2>&1
    Write-Host "Node.js: $nodeVersion" -ForegroundColor Green
}
catch {
    Write-Error "Node.js is not installed. Download from https://nodejs.org/"
    exit 1
}

# Check if dependencies are installed
$nodeModules = Join-Path $apiDir "node_modules"
if (-not (Test-Path $nodeModules)) {
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    Push-Location $apiDir
    & npm install
    Pop-Location
}

# Start the server
Write-Host ""
Write-Host "Starting GPT Web API server..." -ForegroundColor Yellow
Write-Host "API will be available at: http://localhost:$Port/api/chat" -ForegroundColor Cyan
Write-Host ""
Write-Host "First request will prompt for ChatGPT login (5 minute window)" -ForegroundColor Yellow
Write-Host "Subsequent requests will use saved session" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Gray
Write-Host ""

$env:PORT = $Port
$env:HEADLESS = $headlessValue.ToString().ToLowerInvariant()

Push-Location $apiDir
try {
    # Always run directly (blocking) when started by supervisor
    & node server.js
}
finally {
    Pop-Location
}
