# Stripe Payment Bridge Setup Guide

## Overview

The Lantern OS payment bridge enables invoice creation, sending, and payment confirmation through Stripe. This guide walks through obtaining test/live keys and configuring the system.

## Prerequisites

- Stripe account (free to create at https://stripe.com)
- Payment bridge repo (already included)
- PowerShell or bash for running configuration

## Step 1: Create/Access Stripe Account

1. Go to https://stripe.com
2. Sign up or log in
3. Navigate to Dashboard → Developers → API Keys

## Step 2: Get Test Keys (Recommended First)

**Test mode** allows full payment workflow without real charges:

1. In Stripe Dashboard, ensure **Test mode** is enabled (toggle top-right)
2. Go to **API Keys** tab
3. Copy:
   - **Secret Key** (starts with `sk_test_`)
   - **Publishable Key** (starts with `pk_test_`)

Format:
- Secret Key: `sk_test_...` (50+ characters)
- Publishable Key: `pk_test_...` (50+ characters)

## Step 3: Configure Webhook

Webhooks notify your system when payments succeed or fail.

1. In Stripe Dashboard, go to **Webhooks** (left sidebar under Developers)
2. Click **+ Add endpoint**
3. Set **Endpoint URL** to:
   - Development: `http://localhost:3000/api/payment/webhook`
   - Production: `https://yourdomain.com/api/payment/webhook`
4. Select events to listen for:
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
   - `charge.refunded` (optional)
5. Click **Add endpoint**
6. Click the endpoint to view details
7. Copy **Signing Secret** (starts with `whsec_`)

## Step 4: Configure Payment Bridge

### Using PowerShell

```powershell
$scriptPath = "scripts/Configure-StripePaymentBridge.ps1"

# Test mode configuration
& $scriptPath `
  -SecretKey "YOUR_TEST_SECRET_KEY" `
  -PublishableKey "YOUR_TEST_PUBLISHABLE_KEY" `
  -WebhookSecret "YOUR_WEBHOOK_SECRET" `
  -Mode test
```

### Using Environment Variables

```bash
export STRIPE_SECRET_KEY="YOUR_TEST_SECRET_KEY"
export STRIPE_PUBLISHABLE_KEY="YOUR_TEST_PUBLISHABLE_KEY"
export STRIPE_WEBHOOK_SECRET="YOUR_WEBHOOK_SECRET"
export STRIPE_MODE="test"

# Then start the server
npm start --prefix apps/lantern-garage
```

### Manual Configuration

Edit `apps/lantern-garage/payment-bridge/config.json`:

```json
{
  "server": {
    "port": 3000
  },
  "security": {
    "rateLimitWindowMs": 900000,
    "rateLimitMaxRequests": 100
  },
  "paymentProviders": {
    "stripe": {
      "enabled": true,
      "mode": "test",
      "secretKey": "YOUR_TEST_SECRET_KEY",
      "publishableKey": "YOUR_TEST_PUBLISHABLE_KEY",
      "webhookSecret": "YOUR_WEBHOOK_SECRET"
    }
  },
  "wallet": {
    "dataPath": "data/wallet",
    "ledgerFile": "ledger.jsonl",
    "walletStateFile": "local-cash-wallet.json"
  }
}
```

## Step 5: Verify Configuration

1. Start the payment bridge:
   ```bash
   npm start --prefix apps/lantern-garage
   ```

2. Check health endpoint:
   ```bash
   curl http://localhost:3000/api/payment/health
   ```

   Expected response:
   ```json
   {
     "status": "ok",
     "stripe": "configured",
     "mode": "test",
     "timestamp": "2026-05-31T12:00:00.000Z"
   }
   ```

3. Get wallet status:
   ```bash
   curl http://localhost:3000/api/payment/wallet-status
   ```

## Step 6: Test Invoice Workflow

### Create Invoice

```bash
curl -X POST http://localhost:3000/api/payment/create-invoice \
  -H "Content-Type: application/json" \
  -d '{
    "invoiceId": "INV-TEST-001"
  }'
```

### Test Payment (Stripe Dashboard)

1. In Stripe Dashboard, go to **Test Data**
2. Use test card: `4242 4242 4242 4242` (any future date, any CVC)
3. Complete payment flow
4. Webhook will update wallet state automatically

## Live Mode (Production)

⚠️ **Live mode processes real payments. Use only when ready.**

### Prerequisites

1. Stripe account verified and activated
2. Business information complete
3. Bank account connected for payouts
4. Live keys obtained from Stripe Dashboard (toggle to **Live mode**)

### Activation

```powershell
& "scripts/Configure-StripePaymentBridge.ps1" `
  -SecretKey "YOUR_LIVE_SECRET_KEY" `
  -PublishableKey "YOUR_LIVE_PUBLISHABLE_KEY" `
  -WebhookSecret "YOUR_WEBHOOK_SECRET" `
  -Mode live
```

**Confirmation required** - script will prompt for explicit confirmation when switching to live.

## Testing Test Cards

Stripe provides test cards for various scenarios:

| Card Number | Use Case |
|---|---|
| 4242 4242 4242 4242 | Successful payment |
| 4000 0000 0000 0002 | Payment declined |
| 4000 0025 0000 3155 | Requires 3D Secure |
| 5555 5555 5555 4444 | Visa alternative |

All use any future expiry date and any 3-digit CVC.

## Troubleshooting

### Webhook not received?

- Verify endpoint URL is accessible
- Check webhook delivery status in Stripe Dashboard → Webhooks → Your endpoint → Events
- Ensure firewall allows inbound connections
- For development, use Stripe CLI to forward webhooks

### Invoice creation fails?

- Verify Stripe is configured: `GET /api/payment/health`
- Check logs: `npm start --prefix apps/lantern-garage` (with debug output)
- Ensure wallet data directory exists: `data/wallet/`

### Payment not updating wallet?

- Check webhook delivery in Stripe Dashboard
- Verify webhook secret matches (typos block signature verification)
- Check application logs for webhook processing errors
- Confirm ledger file is writable: `data/wallet/ledger.jsonl`

## Security Notes

- **Never commit real API keys to git** — use environment variables or `.env` files
- Webhook secret is sensitive — rotate if compromised
- Use test mode for development
- Enable IP whitelisting if available for webhook endpoints
- Monitor webhook failures in Stripe Dashboard

## API Reference

### Health Check
```
GET /api/payment/health
```

Returns Stripe configuration status.

### Wallet Status
```
GET /api/payment/wallet-status
```

Returns current wallet state, pending invoices, received payments.

### Create Invoice
```
POST /api/payment/create-invoice
Content-Type: application/json

{
  "invoiceId": "INV-EXAMPLE-001"
}
```

### Webhook Endpoint
```
POST /api/payment/webhook
```

Listens for Stripe events. No authentication needed (verified via signature).

## Next Steps

1. ✅ Configure Stripe keys using PowerShell script
2. ✅ Start payment bridge (`npm start`)
3. ✅ Test with test card in Stripe Dashboard
4. ✅ Verify invoice creation and wallet updates
5. ✅ Document real payment testing procedure
6. Move to live mode when ready for production

## Support

For Stripe API issues, consult:
- https://stripe.com/docs/payments
- https://stripe.com/docs/webhooks
- https://stripe.com/docs/testing

For Lantern OS payment bridge issues, check:
- `apps/lantern-garage/payment-bridge/index.js` (server code)
- `apps/lantern-garage/payment-bridge/test.js` (unit tests)
- `data/wallet/ledger.jsonl` (transaction log)
