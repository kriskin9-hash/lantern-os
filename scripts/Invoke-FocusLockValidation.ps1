# ================================================
# Lantern OS - Focus Lock Validation v1.0
# Local script to check if a PR or branch passes focus lock
# ================================================

<#
.SYNOPSIS
    Validate that current work passes the hard focus lock.
.DESCRIPTION
    Loads shipping milestones, checks if trading agent and dream journal
    have shipped. If not, validates that the current branch/PR references
    one of the allowed focus topics.
.PARAMETER PrTitle
    PR title to validate (simulates CI check locally)
.PARAMETER PrBody
    PR body to validate
.PARAMETER CheckShippedOnly
    Only check milestone shipped status; do not enforce lock
.EXAMPLE
    .\Invoke-FocusLockValidation.ps1 -PrTitle "feat(trade): update Kalshi paper positions"
    .\Invoke-FocusLockValidation.ps1 -CheckShippedOnly
#>

param(
    [string]$PrTitle = "",
    [string]$PrBody = "",
    [switch]$CheckShippedOnly = $false
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

function Read-ShippingMilestones {
    $path = Join-Path $RepoRoot "manifests\shipping-milestones.json"
    if (-not (Test-Path $path)) {
        throw "Shipping milestones manifest not found at $path"
    }
    return Get-Content $path -Raw | ConvertFrom-Json
}

function Test-MilestoneShipped {
    param([psobject]$Milestone)
    [bool]$result = $true
    foreach ($prop in $Milestone.definitionOfShipped.PSObject.Properties) {
        if (-not $prop.Value) {
            $result = $false
            Write-Host "    $($prop.Name): FAIL" -ForegroundColor Red
        } else {
            Write-Host "    $($prop.Name): PASS" -ForegroundColor Green
        }
    }
    return $result
}

function Test-PrAgainstFocusLock {
    param([string]$Title, [string]$Body, [string[]]$AllowedTopics)
    $combined = ($Title + " " + $Body).ToLower()
    $matched = $AllowedTopics | Where-Object { $combined -like "*$_*" }
    return $matched
}

# ─── MAIN ──────────────────────────────────────

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "     LANTERN OS - FOCUS LOCK VALIDATION v1.0" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$manifest = Read-ShippingMilestones

Write-Host "`n=== SHIPPING MILESTONES ===" -ForegroundColor Yellow

$dream = $manifest.milestones | Where-Object { $_.id -eq "DREAM-JOURNAL-v1" }
$trading = $manifest.milestones | Where-Object { $_.id -eq "TRADING-AGENT-v1" }

Write-Host "Dream Journal ($($dream.name)):" -ForegroundColor White
$dreamShipped = Test-MilestoneShipped -Milestone $dream

Write-Host "Trading Agent ($($trading.name)):" -ForegroundColor White
$tradingShipped = Test-MilestoneShipped -Milestone $trading

$bothShipped = $dreamShipped -and $tradingShipped

Write-Host "`nFocus Lock Status:" -ForegroundColor Yellow
if ($bothShipped) {
    Write-Host "  DISABLED — Both milestones shipped. All PR topics allowed." -ForegroundColor Green
    exit 0
}

Write-Host "  ACTIVE — Hard lock until both milestones ship." -ForegroundColor Red

if ($CheckShippedOnly) {
    Write-Host "`nCheckShippedOnly mode: returning without PR validation." -ForegroundColor Gray
    exit 0
}

# Validate PR title/body
if ([string]::IsNullOrWhiteSpace($PrTitle) -and [string]::IsNullOrWhiteSpace($PrBody)) {
    Write-Host "`nNo PR title/body provided. Use -PrTitle and -PrBody to validate." -ForegroundColor Gray
    Write-Host "Allowed topics:" -ForegroundColor White
    $manifest.focusLock.allowedTopics | ForEach-Object { Write-Host "  - $_" }
    exit 0
}

Write-Host "`n=== PR VALIDATION ===" -ForegroundColor Yellow
Write-Host "Title: $PrTitle" -ForegroundColor White
Write-Host "Body:  $PrBody" -ForegroundColor White

$matched = Test-PrAgainstFocusLock -Title $PrTitle -Body $PrBody -AllowedTopics $manifest.focusLock.allowedTopics

if ($matched) {
    Write-Host "`nPASS: PR references allowed focus topics:" -ForegroundColor Green
    $matched | ForEach-Object { Write-Host "  -> $_" -ForegroundColor Cyan }
    exit 0
} else {
    Write-Host "`nFAIL: Focus lock ACTIVE." -ForegroundColor Red
    Write-Host "PR does not reference any allowed topic." -ForegroundColor Red
    Write-Host "Allowed topics:" -ForegroundColor White
    $manifest.focusLock.allowedTopics | ForEach-Object { Write-Host "  - $_" }
    exit 1
}
