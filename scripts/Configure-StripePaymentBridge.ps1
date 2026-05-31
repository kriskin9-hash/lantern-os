param(
    [string]$SecretKey,
    [string]$PublishableKey,
    [string]$WebhookSecret,
    [string]$Mode = "test",
    [string]$ConfigPath = "apps/lantern-garage/payment-bridge/config.json"
)

$ErrorActionPreference = "Stop"

function Test-StripeKeys {
    param(
        [string]$SecretKey,
        [string]$PublishableKey,
        [string]$WebhookSecret
    )

    $errors = @()

    if (-not $SecretKey -or -not $SecretKey.StartsWith("sk_")) {
        $errors += "Secret Key must start with 'sk_' (test: sk_test_, live: sk_live_)"
    }

    if (-not $PublishableKey -or -not $PublishableKey.StartsWith("pk_")) {
        $errors += "Publishable Key must start with 'pk_' (test: pk_test_, live: pk_live_)"
    }

    if (-not $WebhookSecret -or -not $WebhookSecret.StartsWith("whsec_")) {
        $errors += "Webhook Secret must start with 'whsec_'"
    }

    # Check mode consistency
    if ($SecretKey.Contains("sk_test_") -and $Mode -eq "live") {
        $errors += "Test secret key but Mode=live. Use sk_live_ key or Mode=test"
    }

    if ($SecretKey.Contains("sk_live_") -and $Mode -eq "test") {
        $errors += "Live secret key but Mode=test. Use Mode=live (requires explicit confirmation)"
    }

    return $errors
}

function Update-PaymentBridgeConfig {
    param(
        [string]$ConfigPath,
        [string]$SecretKey,
        [string]$PublishableKey,
        [string]$WebhookSecret,
        [string]$Mode
    )

    $root = Resolve-Path (Join-Path $PSScriptRoot "..").Path
    $fullPath = Join-Path $root $ConfigPath
    $dir = Split-Path -Parent $fullPath

    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
    }

    $config = @{
        server = @{
            port = 3000
        }
        security = @{
            rateLimitWindowMs = 900000
            rateLimitMaxRequests = 100
        }
        paymentProviders = @{
            stripe = @{
                enabled = $true
                mode = $Mode
                secretKey = $SecretKey
                publishableKey = $PublishableKey
                webhookSecret = $WebhookSecret
            }
        }
        wallet = @{
            dataPath = "data/wallet"
            ledgerFile = "ledger.jsonl"
            walletStateFile = "local-cash-wallet.json"
        }
    }

    $json = $config | ConvertTo-Json -Depth 10
    Set-Content -LiteralPath $fullPath -Value $json -Encoding UTF8

    Write-Host "✓ Configuration saved to: $fullPath"
    Write-Host "  Mode: $Mode"
    Write-Host "  Secret Key: $($SecretKey.Substring(0, 10))..."
    Write-Host "  Publishable Key: $($PublishableKey.Substring(0, 12))..."
}

# Validate inputs
if (-not $SecretKey -or -not $PublishableKey -or -not $WebhookSecret) {
    Write-Host @"
Usage: Configure-StripePaymentBridge.ps1 -SecretKey <key> -PublishableKey <key> -WebhookSecret <secret> [-Mode test|live]

Environment variables (fallback):
  STRIPE_SECRET_KEY
  STRIPE_PUBLISHABLE_KEY
  STRIPE_WEBHOOK_SECRET
  STRIPE_MODE (default: test)

Example (test mode):
  Configure-StripePaymentBridge.ps1 `
    -SecretKey "sk_test_xxx" `
    -PublishableKey "pk_test_xxx" `
    -WebhookSecret "whsec_xxx"

To get keys:
  1. Go to https://dashboard.stripe.com/apikeys
  2. Copy test or live keys
  3. Go to https://dashboard.stripe.com/webhooks
  4. Create webhook for http://localhost:3000/api/payment/webhook
  5. Copy Signing Secret (starts with whsec_)
"@
    exit 1
}

# Test keys
$validationErrors = Test-StripeKeys -SecretKey $SecretKey -PublishableKey $PublishableKey -WebhookSecret $WebhookSecret

if ($validationErrors.Count -gt 0) {
    Write-Host "✗ Validation errors:"
    $validationErrors | ForEach-Object { Write-Host "  - $_" }
    exit 1
}

# Confirm live mode
if ($Mode -eq "live") {
    Write-Host "⚠️  WARNING: Configuring LIVE Stripe keys"
    Write-Host "   This will process real payments."
    $confirm = Read-Host "Type 'I confirm' to proceed with LIVE configuration"
    if ($confirm -ne "I confirm") {
        Write-Host "Cancelled."
        exit 1
    }
}

# Update config
Update-PaymentBridgeConfig -ConfigPath $ConfigPath -SecretKey $SecretKey -PublishableKey $PublishableKey -WebhookSecret $WebhookSecret -Mode $Mode

Write-Host ""
Write-Host "✓ Stripe payment bridge configured"
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Start payment bridge: npm start --prefix apps/lantern-garage"
Write-Host "  2. Test health: curl http://localhost:3000/api/payment/health"
Write-Host "  3. Create test invoice: curl -X POST http://localhost:3000/api/payment/create-invoice ..."
Write-Host ""
