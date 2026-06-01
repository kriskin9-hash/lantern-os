# Stripe Configuration Instructions for Alexander Place

## ✅ Congratulations on Successful Setup

You've successfully:
- ✅ AWS Activate Credits - $1,000 secured
- ✅ Stripe Account - Created and verified
- ❌ Google Cloud - Blocked (we'll address this)

## 🔧 Configure Payment Bridge with Your Stripe Credentials

### Step 1: Get Your Stripe API Keys (2 minutes)
1. Go to Stripe Dashboard: https://dashboard.stripe.com/test/apikeys
2. You'll see your keys already displayed:
   - **Publishable key**: Starts with `pk_test_...`
   - **Secret key**: Starts with `sk_test_...`
   - **Webhook signing secret**: You'll create this next

### Step 2: Configure Payment Bridge (5 minutes)

Edit the config file I created:
```bash
cd apps/lantern-garage/payment-bridge
notepad config.json
```

Replace the placeholder keys with your actual keys:

```json
{
  "paymentProviders": {
    "stripe": {
      "enabled": true,
      "mode": "test",
      "publishableKey": "pk_test_YOUR_ACTUAL_PUBLISHABLE_KEY",
      "secretKey": "sk_test_YOUR_ACTUAL_SECRET_KEY",
      "webhookSecret": "whsec_YOUR_WEBHOOK_SECRET",
      "defaultCurrency": "USD",
      "connectedAccountId": null
    }
  }
}
```

**Replace with your actual keys from Stripe Dashboard**

### Step 3: Setup Webhook (3 minutes)

1. In Stripe Dashboard, go to: Developers → Webhooks → Add endpoint
2. Endpoint URL: `http://localhost:3000/api/payment/webhook`
3. Events to listen for:
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
   - `payment_intent.succeeded`
   - `payment_intent.payment_failed`
4. Copy the webhook signing secret (starts with `whsec_...`)
5. Add it to your config.json

### Step 4: Test Payment Bridge (2 minutes)

```bash
cd apps/lantern-garage/payment-bridge
npm start
```

In another terminal, test the health endpoint:
```bash
curl http://localhost:3000/api/payment/health
```

Expected response:
```json
{
  "status": "ok",
  "stripe": "configured",
  "mode": "test",
  "timestamp": "2026-05-29..."
}
```

## 🧪 Test Payment Flow

### Test Invoice Creation:
```bash
curl -X POST http://localhost:3000/api/payment/create-invoice \
  -H "Content-Type: application/json" \
  -d '{"invoiceId": "INV-COMET-LEAP-RAG-001"}'
```

This will:
- Create a Stripe invoice from your wallet data
- Generate a payment link
- Update your ledger
- Return the invoice URL

## 📊 Validate Your Current Wallet Status

Your wallet shows:
- **Cleared Cash**: $0
- **Pending Invoice**: $199 (INV-COMET-LEAP-RAG-001)
- **Service Offers**: 5 active packages
- **Status**: Ready to send first invoice

## 🌐 Google Cloud Block Troubleshooting

### Common Block Reasons:
1. **Location restrictions** - Some regions have different policies
2. **Application volume** - High volume can trigger temporary blocks
3. **Business verification** - Additional documentation needed

### Solutions:
1. **Wait 24-48 hours** - Temporary blocks often auto-resolve
2. **Try different application path** - Apply through Google Cloud Console instead
3. **Contact support** - Reach out to Google Cloud for Startups support
4. **Alternative approach** - Use AWS credits first, circle back to Google later

## 💰 Current Funding Status

### Secured:
- ✅ AWS Activate: $1,000 credits
- ✅ Stripe: Ready to process payments

### Pending:
- ⏳ Google Cloud: Blocked (will retry later)
- ⏳ Kickstarter: Ready to launch when you're ready
- ⏳ GitHub Sponsors: Ready to activate

### Next Priority:
1. **Configure Stripe credentials** (10 minutes)
2. **Test payment bridge** (5 minutes)
3. **Send first invoice** (2 minutes)
4. **Launch Kickstarter** (2 hours preparation)

## 🎯 Your First Revenue Target

Once Stripe is configured, you can immediately:
1. Send the pending $199 invoice
2. Accept payment via Stripe
3. Update wallet automatically
4. Generate $199 in first revenue

---

## ⚡ Immediate Action Required

**Right now** (10 minutes total):
1. Get Stripe API keys from dashboard (2 min)
2. Edit config.json with actual keys (5 min)
3. Setup webhook endpoint (3 min)
4. Test payment bridge (2 min)
5. Send first invoice (2 min)

**This will activate your entire payment processing system and enable you to generate your first revenue immediately.**

Let me know once you've added your Stripe credentials and I'll help you test the full payment flow!