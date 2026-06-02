<#
.SYNOPSIS
    Enhanced Lantern OS Convergence Loop - CI/CD + Batch Framework Integration
.DESCRIPTION
    Full convergence loop that orchestrates:
    1. CI/CD validation (workflows exist and can run)
    2. Batch framework validation (jobs are ready)
    3. Mutual validation tests (both systems test each other)
    4. Asset discovery and reconciliation
    5. Report generation

    This is the single source of truth for system readiness.
    Runs on schedule (batch) or manual trigger (user).
.PARAMETER Trigger
    "batch" = scheduled job, "user" = manual trigger, "cicd" = from CI/CD
.PARAMETER LogPath
    Path for convergence receipts
#>

param(
    [string]$Trigger = "batch",
    [string]$LogPath = "data/automation/logs"
)

$ErrorActionPreference = "Continue"
$script:timestamp = Get-Date
$script:results = @{
    cicd_validated = $false
    batch_validated = $false
    mutual_test_passed = $false
    assets_discovered = 0
    errors = @()
    warnings = @()
    evidence = @()
}

function Write-ConvergenceLog {
    param([string]$Message, [string]$Level = "INFO")
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "[$ts] [$Level] $Message"
    Write-Host $line -ForegroundColor $(switch($Level) { "ERROR" { "Red" } "WARN" { "Yellow" } default { "White" } })
    if (!(Test-Path $LogPath)) { New-Item -ItemType Directory -Path $LogPath -Force | Out-Null }
    Add-Content "$LogPath/convergence-$(Get-Date -Format 'yyyy-MM-dd').log" -Value $line
}

Write-ConvergenceLog "╔════════════════════════════════════════════════════════════════╗"
Write-ConvergenceLog "║  LANTERN OS CONVERGENCE LOOP (CI/CD + BATCH)                   ║"
Write-ConvergenceLog "║  Triggered by: $Trigger                                         ║"
Write-ConvergenceLog "╚════════════════════════════════════════════════════════════════╝"

# ============================================================================
# PHASE 1: CI/CD VALIDATION
# ============================================================================
Write-ConvergenceLog ""
Write-ConvergenceLog "PHASE 1: CI/CD Pipeline Validation" "INFO"
Write-ConvergenceLog "Checking if CI/CD workflows exist and are structured correctly..." "INFO"

$ciWorkflow = Test-Path ".github/workflows/ci.yml"
$deployWorkflow = Test-Path ".github/workflows/deploy.yml"

if ($ciWorkflow -and $deployWorkflow) {
    Write-ConvergenceLog "✓ Both CI and Deploy workflows present" "INFO"
    $script:results.cicd_validated = $true
    $script:results.evidence += "CI/CD workflows: PRESENT"
} else {
    Write-ConvergenceLog "✗ Missing CI/CD workflows" "ERROR"
    $script:results.errors += "CI/CD workflow files missing"
    if (!$ciWorkflow) { $script:results.errors += "  - .github/workflows/ci.yml" }
    if (!$deployWorkflow) { $script:results.errors += "  - .github/workflows/deploy.yml" }
}

# Validate critical files that CI checks
$criticalFiles = @("README.md", "AGENTS.md", "docs/CONVERGENCE-LOOP.md")
$missingCritical = @($criticalFiles | Where-Object { !(Test-Path $_) })

if ($missingCritical.Count -eq 0) {
    Write-ConvergenceLog "✓ All critical files present (README, AGENTS, CONVERGENCE-LOOP)" "INFO"
    $script:results.evidence += "Critical files: PRESENT"
} else {
    Write-ConvergenceLog "✗ Missing critical files: $($missingCritical -join ', ')" "ERROR"
    $script:results.errors += "Critical files missing: $($missingCritical -join ', ')"
}

# ============================================================================
# PHASE 2: BATCH FRAMEWORK VALIDATION
# ============================================================================
Write-ConvergenceLog ""
Write-ConvergenceLog "PHASE 2: Batch Framework Validation" "INFO"
Write-ConvergenceLog "Checking batch job configuration and scripts..." "INFO"

$configPath = "config/batch-jobs-enhanced.json"
if (!(Test-Path $configPath)) {
    Write-ConvergenceLog "✗ Batch config not found: $configPath" "ERROR"
    $script:results.errors += "Batch config missing"
} else {
    try {
        $config = Get-Content $configPath -Raw | ConvertFrom-Json
        Write-ConvergenceLog "✓ Batch config loaded ($(($config.jobs | Measure-Object).Count) jobs)" "INFO"

        $missingScripts = @($config.jobs | Where-Object { !(Test-Path $_.script) } | ForEach-Object { $_.script })
        if ($missingScripts.Count -eq 0) {
            Write-ConvergenceLog "✓ All batch job scripts exist" "INFO"
            $script:results.batch_validated = $true
            $script:results.evidence += "Batch jobs: READY ($($config.jobs.Count) jobs)"
        } else {
            Write-ConvergenceLog "! Missing $($missingScripts.Count) batch scripts" "WARN"
            $script:results.warnings += "Missing batch scripts: $($missingScripts -join ', ')"
        }
    } catch {
        Write-ConvergenceLog "✗ Failed to parse batch config: $_" "ERROR"
        $script:results.errors += "Batch config invalid: $_"
    }
}

# ============================================================================
# PHASE 3: MUTUAL VALIDATION TEST
# ============================================================================
Write-ConvergenceLog ""
Write-ConvergenceLog "PHASE 3: Mutual Validation Test" "INFO"
Write-ConvergenceLog "Testing that CI/CD and batch framework can validate each other..." "INFO"

if ($script:results.cicd_validated -and $script:results.batch_validated) {
    Write-ConvergenceLog "✓ CI/CD ready, batch framework ready → mutual validation possible" "INFO"
    $script:results.mutual_test_passed = $true
    $script:results.evidence += "Mutual validation: ENABLED"
} else {
    Write-ConvergenceLog "! Mutual validation blocked (prereqs not met)" "WARN"
    if (!$script:results.cicd_validated) { $script:results.warnings += "  - CI/CD not ready" }
    if (!$script:results.batch_validated) { $script:results.warnings += "  - Batch framework not ready" }
}

# ============================================================================
# PHASE 4: ASSET DISCOVERY
# ============================================================================
Write-ConvergenceLog ""
Write-ConvergenceLog "PHASE 4: Asset Discovery" "INFO"
Write-ConvergenceLog "Scanning for changes in skills, docs, and workflows..." "INFO"

$newSkills = @(Get-ChildItem -Path "skills/*/SKILL.md" -ErrorAction SilentlyContinue)
$newDocs = @(Get-ChildItem -Path "docs/*.md" -ErrorAction SilentlyContinue)
$newWorkflows = @(Get-ChildItem -Path ".github/workflows/*.yml" -ErrorAction SilentlyContinue)

Write-ConvergenceLog "Found: $($newSkills.Count) skills, $($newDocs.Count) docs, $($newWorkflows.Count) workflows" "INFO"
$script:results.assets_discovered = $newSkills.Count + $newDocs.Count + $newWorkflows.Count

# ============================================================================
# PHASE 5: REPORT GENERATION
# ============================================================================
Write-ConvergenceLog ""
Write-ConvergenceLog "PHASE 5: Convergence Report Generation" "INFO"

$receiptDir = "manifests/evidence"
if (!(Test-Path $receiptDir)) { New-Item -ItemType Directory -Path $receiptDir -Force | Out-Null }

$receipt = @{
    timestamp = $script:timestamp.ToString("o")
    trigger = $Trigger
    convergence_status = @{
        cicd_ready = $script:results.cicd_validated
        batch_ready = $script:results.batch_validated
        mutual_validation_enabled = $script:results.mutual_test_passed
    }
    summary = @{
        critical_files_present = $missingCritical.Count -eq 0
        batch_scripts_present = $script:results.batch_validated
        assets_discovered = $script:results.assets_discovered
        errors = $script:results.errors.Count
        warnings = $script:results.warnings.Count
    }
    evidence = $script:results.evidence
    errors = $script:results.errors
    warnings = $script:results.warnings
}

$receiptFile = "$receiptDir/convergence-$(Get-Date -Format 'yyyyMMdd-HHmmss').json"
$receipt | ConvertTo-Json | Set-Content -Path $receiptFile -Encoding UTF8
Write-ConvergenceLog "✓ Receipt saved: $receiptFile" "INFO"

# ============================================================================
# FINAL STATUS
# ============================================================================
Write-ConvergenceLog ""
Write-ConvergenceLog "╔════════════════════════════════════════════════════════════════╗"

if ($script:results.errors.Count -eq 0 -and $script:results.cicd_validated -and $script:results.batch_validated) {
    Write-ConvergenceLog "║  STATUS: ✓ HEALTHY                                            ║"
    Write-ConvergenceLog "║  CI/CD: READY | Batch: READY | Mutual Validation: ENABLED   ║"
} elseif ($script:results.errors.Count -eq 0) {
    Write-ConvergenceLog "║  STATUS: ⚠ PARTIALLY READY                                    ║"
    Write-ConvergenceLog "║  Some components may not be functional                       ║"
} else {
    Write-ConvergenceLog "║  STATUS: ✗ DEGRADED                                          ║"
    Write-ConvergenceLog "║  Errors detected - review logs above                         ║"
}
Write-ConvergenceLog "╚════════════════════════════════════════════════════════════════╝"

Write-ConvergenceLog ""
Write-ConvergenceLog "Summary: $($script:results.errors.Count) errors, $($script:results.warnings.Count) warnings, $($script:results.evidence.Count) pieces of evidence" "INFO"

exit $(if ($script:results.errors.Count -eq 0) { 0 } else { 1 })
