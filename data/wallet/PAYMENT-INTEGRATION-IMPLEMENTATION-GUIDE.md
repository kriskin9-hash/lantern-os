# Lantern OS Wallet Payment Integration Implementation Guide

Generated: 2026-05-29

Purpose: Technical implementation guide for integrating payment processors with the Lantern OS wallet system.

## Current System Architecture

### Existing Components
- `data/wallet/local-cash-wallet.json` - State snapshot
- `data/wallet/ledger.jsonl` - Append-only event stream  
- `data/wallet/invoices/` - Invoice drafts in Markdown
- `data/wallet/license-wallet.schema.json` - License wallet structure

### Current Limitations
- No connection to payment processors
- Manual payment status tracking
- No automatic bank transfers
- Limited to invoice generation and tracking

## Technical Integration Architecture

### Proposed Integration Layer

```
┌─────────────────┐
│  Lantern OS     │
│  Wallet System   │
└────────┬────────┘
         │
         │ wallet-bridge.js
         │
┌────────▼────────┐
│  Payment        │
│  Integration    │
│  Layer          │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐ ┌──▼─────────┐
│ Stripe│ │ PayPal     │
│ API   │ │ API        │
└───────┘ └────────────┘
```

## Implementation Plan

### Phase 1: Stripe Integration (Primary Payment Method)

#### 1.1 Setup and Configuration

Create payment configuration structure:
```json
{
  "paymentProviders": {
    "stripe": {
      "enabled": true,
      "mode": "test", // or "live"
      "publishableKey": "pk_test_...",
      "secretKey": "sk_test_...", // Never commit this
      "webhookSecret": "whsec_...", // Never commit this
      "defaultCurrency": "USD",
      "connectedAccountId": null // If using Connect
    }
  },
  "bankAccounts": {
    "primary": {
      "stripeAccountId": "ba_...",
      "last4": "1234",
      "bankName": "Chase"
    }
  }
}
```

#### 1.2 Invoice Conversion Module

Create `apps/lantern-garage/payment-bridge/stripe-invoice-converter.js`:

```javascript
const fs = require('fs');
const path = require('path');

function convertLanternInvoiceToStripe(invoicePath) {
  // Read Lantern invoice markdown
  const invoiceContent = fs.readFileSync(invoicePath, 'utf8');
  
  // Parse invoice details from markdown
  const invoiceData = parseLanternInvoice(invoiceContent);
  
  // Convert to Stripe format
  const stripeInvoice = {
    customer: invoiceData.customerEmail,
    description: invoiceData.description,
    currency: 'usd',
    items: invoiceData.lineItems.map(item => ({
      amount: Math.round(item.amount * 100), // Convert to cents
      currency: 'usd',
      description: item.description,
      quantity: item.quantity || 1
    })),
    due_date: Math.floor(new Date(invoiceData.dueDate).getTime() / 1000),
    metadata: {
      lantern_invoice_id: invoiceData.invoiceId,
      lantern_offer: invoiceData.offer,
      generated_by: 'lantern-os'
    }
  };
  
  return stripeInvoice;
}

function parseLanternInvoice(markdown) {
  // Parse markdown invoice format
  const lines = markdown.split('\n');
  const invoiceData = {
    invoiceId: '',
    customerEmail: '',
    description: '',
    dueDate: '',
    lineItems: []
  };
  
  // Extract invoice details
  lines.forEach(line => {
    if (line.startsWith('# Invoice:')) {
      invoiceData.invoiceId = line.replace('# Invoice:', '').trim();
    } else if (line.startsWith('Customer Email:')) {
      invoiceData.customerEmail = line.replace('Customer Email:', '').trim();
    } else if (line.startsWith('Description:')) {
      invoiceData.description = line.replace('Description:', '').trim();
    } else if (line.startsWith('Due Date:')) {
      invoiceData.dueDate = line.replace('Due Date:', '').trim();
    }
  });
  
  return invoiceData;
}

module.exports = { convertLanternInvoiceToStripe, parseLanternInvoice };
```

#### 1.3 Payment Bridge Service

Create `apps/lantern-garage/payment-bridge/index.js`:

```javascript
const express = require('express');
const stripe = require('stripe')(process.env.STRIPE_SECRET_KEY);
const bodyParser = require('body-parser');
const crypto = require('crypto');

const app = express();
app.use(bodyParser.json());

// Invoice creation endpoint
app.post('/api/payment/create-invoice', async (req, res) => {
  try {
    const { invoicePath, customerEmail } = req.body;
    
    // Convert Lantern invoice to Stripe format
    const stripeInvoiceData = convertLanternInvoiceToStripe(invoicePath);
    
    // Create Stripe invoice
    const invoice = await stripe.invoices.create({
      customer: customerEmail,
      description: stripeInvoiceData.description,
      currency: stripeInvoiceData.currency,
      due_date: stripeInvoiceData.due_date,
      metadata: stripeInvoiceData.metadata
    });
    
    // Add line items
    for (const item of stripeInvoiceData.items) {
      await stripe.invoiceItems.create({
        customer: customerEmail,
        amount: item.amount,
        currency: item.currency,
        description: item.description,
        invoice: invoice.id
      });
    }
    
    // Finalize and send invoice
    const finalizedInvoice = await stripe.invoices.finalizeInvoice(invoice.id);
    const sentInvoice = await stripe.invoices.sendInvoice(finalizedInvoice.id);
    
    // Update Lantern ledger
    updateLedger({
      event: 'stripe_invoice_sent',
      invoiceId: stripeInvoiceData.metadata.lantern_invoice_id,
      stripeInvoiceId: sentInvoice.id,
      stripeInvoiceUrl: sentInvoice.hosted_url,
      timestamp: new Date().toISOString()
    });
    
    res.json({
      success: true,
      invoiceId: sentInvoice.id,
      invoiceUrl: sentInvoice.hosted_url,
      amount: sentInvoice.amount_due / 100
    });
    
  } catch (error) {
    console.error('Invoice creation error:', error);
    res.status(500).json({ success: false, error: error.message });
  }
});

// Webhook endpoint for payment updates
app.post('/api/payment/webhook', async (req, res) => {
  const sig = req.headers['stripe-signature'];
  let event;
  
  try {
    event = stripe.webhooks.constructEvent(req.body, sig, process.env.STRIPE_WEBHOOK_SECRET);
  } catch (err) {
    console.log(`Webhook Error: ${err.message}`);
    return res.status(400).send(`Webhook Error: ${err.message}`);
  }
  
  // Handle the event
  switch (event.type) {
    case 'invoice.payment_succeeded':
      const paymentIntent = event.data.object;
      await handlePaymentSuccess(paymentIntent);
      break;
    case 'invoice.payment_failed':
      const failedPayment = event.data.object;
      await handlePaymentFailure(failedPayment);
      break;
    default:
      console.log(`Unhandled event type ${event.type}`);
  }
  
  res.json({ received: true });
});

async function handlePaymentSuccess(paymentIntent) {
  // Extract Lantern invoice ID from metadata
  const lanternInvoiceId = paymentIntent.metadata.lantern_invoice_id;
  
  // Update Lantern wallet state
  updateWalletState({
    event: 'payment_cleared',
    invoiceId: lanternInvoiceId,
    amount: paymentIntent.amount_received / 100,
    currency: paymentIntent.currency,
    stripePaymentId: paymentIntent.id,
    timestamp: new Date().toISOString()
  });
  
  // Update ledger
  updateLedger({
    event: 'payment_cleared',
    invoiceId: lanternInvoiceId,
    amount: paymentIntent.amount_received / 100,
    stripePaymentId: paymentIntent.id,
    timestamp: new Date().toISOString()
  });
}

async function handlePaymentFailure(paymentIntent) {
  const lanternInvoiceId = paymentIntent.metadata.lantern_invoice_id;
  
  updateLedger({
    event: 'payment_failed',
    invoiceId: lanternInvoiceId,
    stripePaymentId: paymentIntent.id,
    error: paymentIntent.last_payment_error?.message || 'Unknown error',
    timestamp: new Date().toISOString()
  });
}

function updateLedger(event) {
  const ledgerPath = path.join(__dirname, '../../../data/wallet/ledger.jsonl');
  const entry = JSON.stringify(event) + '\n';
  fs.appendFileSync(ledgerPath, entry);
}

function updateWalletState(event) {
  const walletPath = path.join(__dirname, '../../../data/wallet/local-cash-wallet.json');
  const wallet = JSON.parse(fs.readFileSync(walletPath, 'utf8'));
  
  if (event.event === 'payment_cleared') {
    wallet.clearedCashUsd += event.amount;
    // Remove from pending invoices
    wallet.pendingInvoices = wallet.pendingInvoices.filter(
      inv => inv.invoiceId !== event.invoiceId
    );
    wallet.receivedPayments.push({
      invoiceId: event.invoiceId,
      amount: event.amount,
      currency: event.currency,
      clearedAt: event.timestamp,
      stripePaymentId: event.stripePaymentId
    });
  }
  
  fs.writeFileSync(walletPath, JSON.stringify(wallet, null, 2));
}

const PORT = process.env.PAYMENT_BRIDGE_PORT || 3000;
app.listen(PORT, () => {
  console.log(`Payment bridge running on port ${PORT}`);
});
```

#### 1.4 Environment Variables Setup

Create `.env.payment` (never commit this file):
```
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
PAYMENT_BRIDGE_PORT=3000
NODE_ENV=development
```

Update `AGENTS.md` to include:
```
## Environment Variables Required
- Copy .env.payment.example to .env.payment
- Fill in actual Stripe credentials
- Never commit .env.payment to repository
```

### Phase 2: Customer Management

#### 2.1 Customer Creation

```javascript
// Add to payment bridge
app.post('/api/payment/create-customer', async (req, res) => {
  try {
    const { email, name, company } = req.body;
    
    const customer = await stripe.customers.create({
      email: email,
      name: name,
      metadata: {
        company: company || '',
        source: 'lantern-os'
      }
    });
    
    res.json({
      success: true,
      customerId: customer.id,
      customerEmail: customer.email
    });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});
```

#### 2.2 Customer Portal Integration

```javascript
// Add customer portal for self-service payment management
app.post('/api/payment/create-portal-session', async (req, res) => {
  const { customerId, returnUrl } = req.body;
  
  const session = await stripe.billingPortal.sessions.create({
    customer: customerId,
    return_url: returnUrl
  });
  
  res.json({ url: session.url });
});
```

### Phase 3: Bank Transfer Integration

#### 3.1 Stripe Connect for Bank Transfers

```javascript
// Enable bank transfers via Stripe Connect
app.post('/api/payment/setup-bank-account', async (req, res) => {
  try {
    const { accountNumber, routingNumber } = req.body;
    
    // Create external account
    const bankAccount = await stripe.accounts.createExternalAccount(
      process.env.STRIPE_CONNECTED_ACCOUNT_ID,
      {
        external_account: {
          object: 'bank_account',
          country: 'US',
          currency: 'usd',
          account_number: accountNumber,
          routing_number: routingNumber
        }
      }
    );
    
    res.json({
      success: true,
      bankAccountId: bankAccount.id,
      bankName: bankAccount.bank_name
    });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});
```

#### 3.2 Payout Management

```javascript
// Manual payout trigger
app.post('/api/payment/create-payout', async (req, res) => {
  try {
    const { amount } = req.body;
    
    const payout = await stripe.payouts.create({
      amount: Math.round(amount * 100), // Convert to cents
      currency: 'usd'
    });
    
    updateLedger({
      event: 'bank_payout_initiated',
      amount: amount,
      stripePayoutId: payout.id,
      timestamp: new Date().toISOString()
    });
    
    res.json({
      success: true,
      payoutId: payout.id,
      amount: payout.amount / 100,
      arrivalDate: payout.arrival_date
    });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});
```

### Phase 4: Alternative Payment Methods

#### 4.1 PayPal Integration (Optional)

```javascript
// Add PayPal as alternative payment method
const paypal = require('@paypal/payouts-sdk');

paypal.configure({
  mode: process.env.PAYPAL_MODE || 'sandbox',
  client_id: process.env.PAYPAL_CLIENT_ID,
  client_secret: process.env.PAYPAL_CLIENT_SECRET
});

app.post('/api/payment/paypal-create-order', async (req, res) => {
  try {
    const { amount, invoiceId } = req.body;
    
    const request = new paypal.orders.OrdersCreateRequest();
    request.prefer("return=representation");
    request.request_body({
      intent: 'CAPTURE',
      purchase_units: [{
        amount: {
          currency_code: 'USD',
          value: amount.toFixed(2)
        },
        description: `Lantern OS Invoice ${invoiceId}`,
        custom_id: invoiceId
      }]
    });
    
    const order = await paypal.client().execute(request);
    
    res.json({
      success: true,
      orderId: order.result.id,
      approvalUrl: order.result.links.find(link => link.rel === 'approve').href
    });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});
```

## Security Considerations

### 1. API Key Management
```javascript
// Use environment variables exclusively
const stripeSecretKey = process.env.STRIPE_SECRET_KEY;
if (!stripeSecretKey) {
  throw new Error('STRIPE_SECRET_KEY environment variable not set');
}
```

### 2. Webhook Security
```javascript
// Always verify webhook signatures
function verifyWebhookSignature(payload, signature, secret) {
  const hmac = crypto.createHmac('sha256', secret);
  hmac.update(payload);
  const digest = hmac.digest('hex');
  return crypto.timingSafeEqual(
    Buffer.from(signature.split('=')[1], 'hex'),
    Buffer.from(digest, 'hex')
  );
}
```

### 3. Rate Limiting
```javascript
const rateLimit = require('express-rate-limit');

const paymentLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // limit each IP to 100 requests per windowMs
  message: 'Too many payment requests from this IP'
});

app.use('/api/payment/', paymentLimiter);
```

## Testing Strategy

### Test Environment Setup
1. Use Stripe test mode exclusively during development
2. Use Stripe test cards for payment simulation
3. Test webhook delivery with Stripe CLI
4. Validate ledger updates after each transaction

### Test Cases
```javascript
// Example test suite
describe('Payment Integration', () => {
  test('Create invoice from Lantern format', async () => {
    const result = await convertLanternInvoiceToStripe('./test-invoice.md');
    expect(result).toHaveProperty('customer');
    expect(result).toHaveProperty('items');
  });
  
  test('Handle successful payment webhook', async () => {
    const mockPayment = {
      metadata: { lantern_invoice_id: 'TEST-001' },
      amount_received: 19900,
      currency: 'usd',
      id: 'pi_test_123'
    };
    await handlePaymentSuccess(mockPayment);
    // Verify ledger and wallet updates
  });
});
```

## Deployment Considerations

### Production Setup
1. Switch Stripe mode from test to live
2. Use production webhooks (not localhost)
3. Enable SSL/TLS for payment bridge
4. Set up monitoring and alerting
5. Implement proper error handling and retries

### Monitoring
```javascript
// Add logging and monitoring
const winston = require('winston');

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.json(),
  transports: [
    new winston.transports.File({ filename: 'payment-error.log', level: 'error' }),
    new winston.transports.File({ filename: 'payment-combined.log' })
  ]
});

// Use in payment handlers
logger.info('Invoice created', { invoiceId: invoice.id, amount: invoice.amount });
logger.error('Payment failed', { error: error.message, invoiceId: invoice.id });
```

## Integration with Existing Lantern OS Components

### 1. Garage App Integration
```javascript
// Add to apps/lantern-garage/server.js
const paymentBridge = require('./payment-bridge');

// Add payment status to garage dashboard
function getWalletStatus() {
  const wallet = readJson('data/wallet/local-cash-wallet.json');
  const ledger = readJsonl('data/wallet/ledger.jsonl', 10);
  
  return {
    clearedCash: wallet.clearedCashUsd,
    pendingInvoices: wallet.pendingInvoices.length,
    recentActivity: ledger.slice(-5)
  };
}
```

### 2. Skill Integration
```javascript
// Allow skills to trigger invoice creation
async function createInvoiceForSkill(skillName, customerData) {
  const invoiceData = {
    offer: skillName,
    customerEmail: customerData.email,
    amount: getSkillPricing(skillName)
  };
  
  // Generate Lantern invoice
  const invoicePath = generateLanternInvoice(invoiceData);
  
  // Send via Stripe
  await createStripeInvoice(invoicePath, customerData.email);
  
  return { success: true, invoicePath };
}
```

## Backup and Recovery

### Data Protection
```javascript
// Automatic backup before financial operations
function backupBeforeOperation(operation) {
  const timestamp = new Date().toISOString();
  const backupDir = `data/wallet/backups/${timestamp}`;
  fs.mkdirSync(backupDir, { recursive: true });
  
  // Backup critical files
  fs.copyFileSync('data/wallet/local-cash-wallet.json', 
    `${backupDir}/local-cash-wallet.json`);
  fs.copyFileSync('data/wallet/ledger.jsonl', 
    `${backupDir}/ledger.jsonl`);
  
  return operation().catch(error => {
    console.error('Operation failed, backup available at:', backupDir);
    throw error;
  });
}
```

## Legal and Compliance Implementation

### 1. Terms of Service Integration
```javascript
// Add TOS acceptance to customer creation
app.post('/api/payment/create-customer', async (req, res) => {
  const { email, name, tosAccepted } = req.body;
  
  if (!tosAccepted) {
    return res.status(400).json({ 
      success: false, 
      error: 'Terms of service must be accepted' 
    });
  }
  
  // Record TOS acceptance
  updateLedger({
    event: 'tos_accepted',
    customerEmail: email,
    timestamp: new Date().toISOString()
  });
  
  // Proceed with customer creation
  // ...
});
```

### 2. Tax Reporting Preparation
```javascript
// Prepare 1099-K data at year end
function generateTaxReport(year) {
  const ledger = readJsonl('data/wallet/ledger.jsonl');
  const yearPayments = ledger.filter(entry => 
    entry.event === 'payment_cleared' && 
    entry.timestamp.startsWith(year)
  );
  
  return yearPayments.map(payment => ({
    amount: payment.amount,
    date: payment.timestamp,
    invoiceId: payment.invoiceId
  }));
}
```

## Migration Strategy

### From Current System to Integrated System
1. **Phase 1**: Add payment bridge alongside existing system (parallel operation)
2. **Phase 2**: Route new invoices through payment bridge
3. **Phase 3**: Migrate existing pending invoices to payment system
4. **Phase 4**: Deprecate manual invoice tracking
5. **Phase 5**: Remove manual tracking code

### Data Migration Script
```javascript
// Migrate existing invoices to Stripe
async function migrateExistingInvoices() {
  const wallet = JSON.parse(fs.readFileSync('data/wallet/local-cash-wallet.json', 'utf8'));
  
  for (const invoice of wallet.pendingInvoices) {
    if (invoice.status === 'draft_ready_to_send') {
      await createStripeInvoice(invoice.invoicePath, invoice.customerEmail);
      console.log(`Migrated invoice ${invoice.invoiceId}`);
    }
  }
}
```

## Support and Maintenance

### Common Issues
1. **Webhook failures**: Implement retry logic and manual recovery
2. **Payment disputes**: Set up automated dispute handling
3. **Bank transfer delays**: Monitor and alert on long-running transfers
4. **API rate limits**: Implement exponential backoff

### Maintenance Tasks
- Regular webhook endpoint monitoring
- API key rotation (quarterly)
- Compliance review (monthly)
- Security audit (annually)
- Performance optimization (ongoing)

---

This implementation guide provides a comprehensive path to integrate payment processing with the existing Lantern OS wallet system while maintaining security, compliance, and the local-first principles of the current architecture.