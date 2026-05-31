param(
    [string]$ApplicationPath = "applications/SFF-HSEE-2026-DRAFT.md",
    [string]$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [switch]$DryRun,
    [switch]$ValidateOnly
)

$ErrorActionPreference = "Stop"

Write-Host "=== Grant Submission Runner ===" -ForegroundColor Cyan

# Validate application exists
$appFullPath = Join-Path $Root $ApplicationPath
if (-not (Test-Path $appFullPath)) {
    Write-Error "Application not found: $appFullPath"
    exit 1
}

Write-Host "Application: $ApplicationPath" -ForegroundColor White

# Parse application for required sections
$appContent = Get-Content $appFullPath -Raw

$requiredSections = @(
    "Project Summary",
    "Why This Fits",
    "Current State and Evidence",
    "Use of Funds",
    "Theory of Change"
)

$missingSections = @()
foreach ($section in $requiredSections) {
    if ($appContent -notlike "*$section*") {
        $missingSections += $section
    }
}

if ($missingSections.Count -gt 0) {
    Write-Host "`nVALIDATION FAILED: Missing sections:" -ForegroundColor Red
    foreach ($section in $missingSections) {
        Write-Host "  - $section" -ForegroundColor Red
    }
    exit 1
}

Write-Host "`nVALIDATION PASSED: All required sections present" -ForegroundColor Green

# Check for submission URL
$urlMatch = $appContent | Select-String -Pattern "https?://[^\s]+" -AllMatches
$submissionUrls = @()
if ($urlMatch) {
    foreach ($match in $urlMatch.Matches) {
        $url = $match.Value
        if ($url -like "*survivalandflourishing*" -or $url -like "*application*") {
            $submissionUrls += $url
        }
    }
}

Write-Host "`nSubmission URLs found:" -ForegroundColor White
if ($submissionUrls.Count -gt 0) {
    foreach ($url in $submissionUrls | Select-Object -Unique) {
        Write-Host "  - $url" -ForegroundColor Cyan
    }
} else {
    Write-Host "  (None found - check application for URLs)" -ForegroundColor Yellow
}

# Extract deadline
$deadlineLine = $appContent | Select-String -Pattern "Deadline.*(\d{4}-\d{2}-\d{2}|\w+ \d{1,2}, \d{4})"
if ($deadlineLine) {
    Write-Host "`nDeadline: $($deadlineLine.Matches[0].Value)" -ForegroundColor Yellow
    
    # Calculate days remaining
    try {
        $deadlineStr = $deadlineLine.Matches[0].Groups[1].Value
        $deadline = [datetime]::Parse($deadlineStr)
        $daysRemaining = ($deadline - (Get-Date)).Days
        Write-Host "Days remaining: $daysRemaining" -ForegroundColor $(if ($daysRemaining -lt 7) { "Red" } elseif ($daysRemaining -lt 30) { "Yellow" } else { "Green" })
    } catch {
        Write-Host "  (Could not parse deadline)" -ForegroundColor Yellow
    }
}

# Check for operator approval boundary
$boundaryLine = $appContent | Select-String -Pattern "Status.*unvalidated|requires operator|Operator Boundary"
if ($boundaryLine) {
    Write-Host "`nOPERATOR BOUNDARY DETECTED:" -ForegroundColor Red
    Write-Host "  $boundaryLine" -ForegroundColor Red
    Write-Host "`nThis application requires operator approval before submission." -ForegroundColor Red
    $operatorApprovalRequired = $true
} else {
    $operatorApprovalRequired = $false
}

# Generate submission receipt
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$receiptId = "grant-submission-$stamp"

$receipt = [ordered]@{
    receiptId = $receiptId
    generatedAt = (Get-Date).ToString("o")
    evidenceClass = "grant_submission_validation"
    applicationPath = $ApplicationPath
    validationPassed = $true
    missingSections = $missingSections
    submissionUrls = @($submissionUrls | Select-Object -Unique)
    operatorApprovalRequired = $operatorApprovalRequired
    dryRun = $DryRun.IsPresent
    status = $(if ($operatorApprovalRequired) { "blocked_pending_operator" } else { "ready_to_submit" })
    nextAction = $(if ($operatorApprovalRequired) { "Operator must review and approve application" } else { "Visit submission URL and complete application" })
    boundary = "No automated submission without operator approval per AGENTS.md"
}

# Save receipt
$receiptDir = Join-Path $Root "manifests/evidence"
if (-not (Test-Path $receiptDir)) {
    New-Item -ItemType Directory -Path $receiptDir -Force | Out-Null
}

$receiptFile = Join-Path $receiptDir "$receiptId.json"
$receipt | ConvertTo-Json -Depth 5 | Set-Content $receiptFile -Encoding UTF8

Write-Host "`nReceipt: $receiptFile" -ForegroundColor Green

if ($DryRun) {
    Write-Host "`n[DRY RUN] Would submit application if not blocked" -ForegroundColor Yellow
    $receipt | ConvertTo-Json -Depth 5 | Write-Host
}

if ($ValidateOnly) {
    Write-Host "`nValidation complete. Submission not attempted." -ForegroundColor Yellow
    exit 0
}

if ($operatorApprovalRequired) {
    Write-Host "`nSUBMISSION BLOCKED: Operator approval required" -ForegroundColor Red
    Write-Host "Review: $appFullPath" -ForegroundColor White
    Write-Host "Then run with -Force flag if approved (not implemented for safety)" -ForegroundColor Yellow
    exit 1
}

Write-Host "`nApplication ready for manual submission." -ForegroundColor Green
Write-Host "Next: Visit submission URL and complete the application." -ForegroundColor White

exit 0
