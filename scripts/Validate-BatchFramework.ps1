<#
.SYNOPSIS
    Validate batch job framework configuration and readiness
.DESCRIPTION
    CI/CD job that validates the batch framework is healthy and ready to run.
    This allows CI/CD to verify batch jobs will work correctly.
    Part of mutual validation loop - CI/CD validates batch framework.
.PARAMETER ConfigPath
    Path to batch jobs config file
#>

param(
    [string]$ConfigPath = "config/batch-jobs-enhanced.json"
)

$ErrorActionPreference = "Continue"
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$results = @{
    passed = @()
    failed = @()
    warnings = @()
}

Write-Host "`n[$timestamp] === Batch Framework Validation ===" -ForegroundColor Cyan

# ============================================================================
# 1. Check config file exists and is valid JSON
# ============================================================================
Write-Host "[1/5] Validating configuration file..." -NoNewline
if (!(Test-Path $ConfigPath)) {
    Write-Host " ✗" -ForegroundColor Red
    $results.failed += "Config file not found: $ConfigPath"
    exit 1
}

try {
    $config = Get-Content $ConfigPath -Raw | ConvertFrom-Json
    Write-Host " ✓" -ForegroundColor Green
    $results.passed += "Config file valid JSON"
} catch {
    Write-Host " ✗" -ForegroundColor Red
    $results.failed += "Invalid JSON in config: $_"
    exit 1
}

# ============================================================================
# 2. Validate required schema fields
# ============================================================================
Write-Host "[2/5] Validating schema..." -NoNewline
$requiredFields = @("schema", "jobs", "groups", "defaults")
$missingFields = $requiredFields | Where-Object { -not $config.$_ }

if ($missingFields.Count -eq 0) {
    Write-Host " ✓" -ForegroundColor Green
    $results.passed += "Schema contains all required fields"
} else {
    Write-Host " ✗" -ForegroundColor Red
    $results.failed += "Missing schema fields: $($missingFields -join ', ')"
}

# ============================================================================
# 3. Check all referenced scripts exist
# ============================================================================
Write-Host "[3/5] Checking job scripts..." -NoNewline
$missingScripts = @()
foreach ($job in $config.jobs) {
    if (!(Test-Path $job.script)) {
        $missingScripts += $job.script
    }
}

if ($missingScripts.Count -eq 0) {
    Write-Host " ✓" -ForegroundColor Green
    $results.passed += "All $($config.jobs.Count) job scripts exist"
} else {
    Write-Host " ! " -ForegroundColor Yellow
    $results.warnings += "Missing $($missingScripts.Count) job scripts: $($missingScripts -join ', ')"
}

# ============================================================================
# 4. Check log and receipt directories can be created
# ============================================================================
Write-Host "[4/5] Checking output directories..." -NoNewline
$logDir = $config.defaults.logDir
$receiptDir = $config.defaults.receiptDir

try {
    if (!(Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
    if (!(Test-Path $receiptDir)) { New-Item -ItemType Directory -Path $receiptDir -Force | Out-Null }
    Write-Host " ✓" -ForegroundColor Green
    $results.passed += "Log and receipt directories ready"
} catch {
    Write-Host " ✗" -ForegroundColor Red
    $results.failed += "Could not create directories: $_"
}

# ============================================================================
# 5. Validate mutual validation config
# ============================================================================
Write-Host "[5/5] Checking mutual validation setup..." -NoNewline
if ($config.mutualValidationConfig.enabled) {
    Write-Host " ✓" -ForegroundColor Green
    $results.passed += "Mutual validation enabled (batch validates CI/CD, CI/CD validates batch)"
} else {
    Write-Host " ! " -ForegroundColor Yellow
    $results.warnings += "Mutual validation disabled"
}

# ============================================================================
# Summary
# ============================================================================
Write-Host "`n[$timestamp] === Summary ===" -ForegroundColor Cyan
Write-Host "Passed: $($results.passed.Count)" -ForegroundColor Green
Write-Host "Failed: $($results.failed.Count)" -ForegroundColor Red
Write-Host "Warnings: $($results.warnings.Count)" -ForegroundColor Yellow

Write-Host "`nResults:" -ForegroundColor Cyan
$results.passed | ForEach-Object { Write-Host "  ✓ $_" -ForegroundColor Green }
$results.failed | ForEach-Object { Write-Host "  ✗ $_" -ForegroundColor Red }
$results.warnings | ForEach-Object { Write-Host "  ! $_" -ForegroundColor Yellow }

$status = if ($results.failed.Count -eq 0) { "READY" } else { "BROKEN" }
Write-Host "`nBatch Framework Status: $status`n" -ForegroundColor $(if ($status -eq "READY") { "Green" } else { "Red" })

exit $(if ($results.failed.Count -eq 0) { 0 } else { 1 })
