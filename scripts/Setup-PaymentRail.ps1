param(
    [ValidateSet("stripe", "paypal", "github-sponsors", "gumroad")]
    [string]$Provider = "stripe",
    
    [string]$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    
    [switch]$DryRun,
    [switch]$CheckStatus
)

$ErrorActionPreference = "Stop"

Write-Host "=== Payment Rail Setup ===" -ForegroundColor Cyan
Write-Host "Provider: $Provider" -ForegroundColor White

$walletPath = Join-Path $Root "data/wallet/local-cash-wallet.json"
$ledgerPath = Join-Path $Root "data/wallet/ledger.jsonl"

# Check if payment rail already configured
$existingRail = $null
if (Test-Path $walletPath) {
    $wallet = Get-Content $walletPath | ConvertFrom-Json
    $existingRail = $wallet.paymentRail
}

if ($existingRail -and -not $CheckStatus) {
    Write-Host "`nEXISTING PAYMENT RAIL DETECTED: $existingRail" -ForegroundColor Yellow
    Write-Host "Current setup must be cleared before switching." -ForegroundColor Yellow
    
    $receipt = [ordered]@{
        timestamp = (Get-Date).ToString("o")
        event = "payment_rail_setup_blocked"
        provider = $Provider
        existingRail = $existingRail
        reason = "existing_setup_prevents_change"
        status = "manual_clearing_required"
    }
    
    $receipt | ConvertTo-Json -Compress | Add-Content $ledgerPath
    exit 1
}

if ($CheckStatus) {
    Write-Host "`nPAYMENT RAIL STATUS:" -ForegroundColor White
    if ($existingRail) {
        Write-Host "  Provider: $existingRail" -ForegroundColor Green
        Write-Host "  Status: Active" -ForegroundColor Green
        
        # Check for pending invoices
        if ($wallet.pendingInvoices) {
            Write-Host "`n  Pending Invoices:" -ForegroundColor Yellow
            foreach ($inv in $wallet.pendingInvoices) {
                Write-Host "    - $($inv.invoiceId): $($inv.amountUsd) USD ($($inv.status))" -ForegroundColor Yellow
            }
        }
    } else {
        Write-Host "  Provider: None configured" -ForegroundColor Red
        Write-Host "  Status: Blocked - No payment rail" -ForegroundColor Red
        Write-Host "`n  To enable sales, run:" -ForegroundColor White
        Write-Host "    .\scripts\Setup-PaymentRail.ps1 -Provider stripe" -ForegroundColor Cyan
    }
    exit 0
}

# AGENTS.md Boundary Check
Write-Host "`nAGENTS.md SAFETY BOUNDARY:" -ForegroundColor Yellow
Write-Host "Payment rails store secrets (API keys) that must NOT be committed to Git." -ForegroundColor Yellow
Write-Host "Setup requires:" -ForegroundColor White
Write-Host "  1. Provider account (Stripe/PayPal/etc)" -ForegroundColor White
Write-Host "  2. API key stored outside repo (env var or secure vault)" -ForegroundColor White
Write-Host "  3. Public payment link generated" -ForegroundColor White
Write-Host "  4. Test transaction completed" -ForegroundColor White

if (-not $DryRun) {
    Write-Host "`nOPERATOR APPROVAL REQUIRED:" -ForegroundColor Red
    Write-Host "This action configures real payment processing." -ForegroundColor Red
    Write-Host "Have you:" -ForegroundColor White
    Write-Host "  [ ] Created $Provider account" -ForegroundColor White
    Write-Host "  [ ] Verified identity with $Provider" -ForegroundColor White
    Write-Host "  [ ] Obtained API keys" -ForegroundColor White
    Write-Host "  [ ] Stored keys outside Git (env file, vault)" -ForegroundColor White
    
    Write-Host "`nThis script will NOT store API keys in the repo." -ForegroundColor Green
    Write-Host "Manual configuration required per AGENTS.md safety rules." -ForegroundColor Green
}

# Configuration template
$configTemplate = @"
# Payment Rail Configuration for $Provider
# Generated: $(Get-Date -Format "o")
# 
# IMPORTANT: Do NOT commit this file with real credentials.
# Copy to .env.local (gitignored) and fill in values.

PAYMENT_PROVIDER=$Provider
PAYMENT_CURRENCY=USD

# ${Provider} Configuration
# Get these from your ${Provider} dashboard
${Provider}_API_KEY=pk_test_...
${Provider}_WEBHOOK_SECRET=whsec_...

# Public-facing payment link (generated in ${Provider} dashboard)
# This can be shared with customers
PAYMENT_LINK=https://pay.${Provider}.com/...

# Test mode (true for development, false for production)
TEST_MODE=true
"@

$configPath = Join-Path $Root "data/wallet/payment-rail-config.env.example"

if ($DryRun) {
    Write-Host "`n[DRY RUN] Would write config template to:" -ForegroundColor Yellow
    Write-Host "  $configPath" -ForegroundColor Yellow
    Write-Host "`nConfig template:" -ForegroundColor Yellow
    Write-Host $configTemplate -ForegroundColor Gray
} else {
    # Check for .env.local (gitignored)
    $envLocalPath = Join-Path $Root ".env.local"
    $gitignorePath = Join-Path $Root ".gitignore"
    
    $gitignoreHasEnvLocal = $false
    if (Test-Path $gitignorePath) {
        $gitignoreContent = Get-Content $gitignorePath -Raw
        $gitignoreHasEnvLocal = $gitignoreContent -like "*.env.local*" -or $gitignoreContent -like "*.env*"
    }
    
    if (-not $gitignoreHasEnvLocal) {
        Write-Host "`nWARNING: .env.local not in .gitignore" -ForegroundColor Red
        Write-Host "Add this line to .gitignore before storing secrets:" -ForegroundColor Yellow
        Write-Host "  .env.local" -ForegroundColor Cyan
    }
    
    # Write example config (safe to commit)
    $configTemplate | Set-Content $configPath -Encoding UTF8
    Write-Host "`nExample config written: $configPath" -ForegroundColor Green
    
    Write-Host "`nNEXT STEPS (Manual - Required):" -ForegroundColor Cyan
    Write-Host "1. Copy to .env.local (DO NOT COMMIT):" -ForegroundColor White
    Write-Host "   Copy-Item $configPath .env.local" -ForegroundColor Cyan
    Write-Host "2. Fill in your real API keys from $Provider dashboard" -ForegroundColor White
    Write-Host "3. Generate payment link in $Provider dashboard" -ForegroundColor White
    Write-Host "4. Test with $1 transaction" -ForegroundColor White
    Write-Host "5. Update wallet with payment link:" -ForegroundColor White
    Write-Host "   data/wallet/local-cash-wallet.json" -ForegroundColor Cyan
    
    # Generate receipt
    $receipt = [ordered]@{
        timestamp = (Get-Date).ToString("o")
        event = "payment_rail_setup_initiated"
        provider = $Provider
        configTemplatePath = $configPath
        status = "manual_configuration_required"
        gitignoreChecked = $gitignoreHasEnvLocal
        operatorActionRequired = "true"
        nextStep = "Copy config to .env.local and fill in real credentials"
    }
    
    $receipt | ConvertTo-Json -Compress | Add-Content $ledgerPath
    Write-Host "`nReceipt recorded to: $ledgerPath" -ForegroundColor Green
}

exit 0
