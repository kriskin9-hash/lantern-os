# Lantern Payment Bridge Setup Instructions

## Automated Setup Completed ✅

The following infrastructure has been automatically created:

- ✅ Payment bridge server (`index.js`)
- ✅ Stripe invoice converter (`stripe-invoice-converter.js`)  
- ✅ Package configuration (`package.json`)
- ✅ Configuration template (`config.example.json`)

## Manual Setup Required 📋

### Step 1: Install Dependencies
```bash
cd apps/lantern-garage/payment-bridge
npm install
```

### Step 2: Configure Environment
Copy the example configuration and add your credentials:
```bash
cp config.example.json config.json
```

Edit `config.json` and add your Stripe API keys (from Step 3).

### Step 3: Get Stripe API Keys (Manual Action Required)

1. **Create Stripe Account** (You must do this):
   - Go to: https://stripe.com/register
   - Sign up with email and business information
   - Complete KYC verification (business details, personal info)
   - This requires personal identity verification

2. **Get API Keys**:
   - Dashboard → Developers → API keys
   - Copy Publishable key (pk_test_...)
   - Copy Secret key (sk_test_...)
   - Add these to your `config.json`

3. **Setup Webhook**:
   - Dashboard → Developers → Webhooks
   - Add endpoint: `https://your-domain.com/api/payment/webhook`
   - Copy webhook signing secret (whsec_...)
   - Add to `config.json`

### Step 4: Test the Payment Bridge
```bash
# Start the server
npm start

# Test health endpoint
curl http://localhost:3000/api/payment/health
```

### Step 5: Configure with Lantern Garage

Update `apps/lantern-garage/server.js` to integrate with payment bridge.

## Security Notes ⚠️

- Never commit `config.json` to git
- Never share API keys publicly
- Use test mode until fully operational
- Enable webhook signature verification in production

## Next Steps

Once Stripe is configured manually, the payment bridge can:
- Automatically create invoices from wallet data
- Process payments via Stripe
- Update wallet ledger automatically
- Handle webhooks for payment status