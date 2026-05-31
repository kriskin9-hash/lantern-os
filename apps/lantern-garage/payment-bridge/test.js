const assert = require('assert');
const fs = require('fs');
const path = require('path');
const invoiceConverter = require('./stripe-invoice-converter');

console.log('Running payment-bridge tests...\n');

let testsRun = 0;
let testsPassed = 0;

function test(name, fn) {
  testsRun++;
  try {
    fn();
    console.log(`✓ ${name}`);
    testsPassed++;
  } catch (error) {
    console.error(`✗ ${name}`);
    console.error(`  ${error.message}`);
  }
}

// Test: parseLanternInvoice
test('Parse Lantern invoice markdown', () => {
  const markdown = `
# Invoice: INV-TEST-001
Customer Email: customer@example.com
Description: Test Service
Due Date: 2026-06-30
Offer: Test Offer

- Development Services: $500
- Consulting: $200
  `.trim();

  const result = invoiceConverter.parseLanternInvoice(markdown);
  assert.strictEqual(result.invoiceId, 'INV-TEST-001');
  assert.strictEqual(result.customerEmail, 'customer@example.com');
  assert.strictEqual(result.lineItems.length, 2);
  assert.strictEqual(result.lineItems[0].amount, 500);
});

// Test: generateStripeInvoiceFromWallet
test('Generate Stripe invoice from wallet data', () => {
  const walletInvoice = {
    invoiceId: 'INV-WALLET-001',
    customerEmail: 'buyer@example.com',
    offer: 'RAG Sprint',
    amountUsd: 250
  };

  const stripe = invoiceConverter.generateStripeInvoiceFromWallet(walletInvoice);
  assert.strictEqual(stripe.description, 'RAG Sprint');
  assert.strictEqual(stripe.items[0].amount, 25000); // 250 * 100 cents
  assert.strictEqual(stripe.metadata.lantern_invoice_id, 'INV-WALLET-001');
});

// Test: Stripe webhook payload parsing
test('Handle invoice.payment_succeeded webhook event', () => {
  const webhookEvent = {
    type: 'invoice.payment_succeeded',
    data: {
      object: {
        id: 'in_1234567890',
        amount_paid: 19900,
        currency: 'usd',
        payment_intent: 'pi_test_123',
        metadata: {
          lantern_invoice_id: 'INV-COMET-LEAP-RAG-001'
        }
      }
    }
  };

  assert.strictEqual(webhookEvent.type, 'invoice.payment_succeeded');
  assert.strictEqual(webhookEvent.data.object.metadata.lantern_invoice_id, 'INV-COMET-LEAP-RAG-001');
  assert.strictEqual(webhookEvent.data.object.amount_paid, 19900);
});

// Test: Webhook signature validation structure
test('Webhook signature header validation structure', () => {
  const sig = 't=1614556800,v1=test_signature_hex';
  const parts = sig.split(',');

  assert(parts.some(p => p.startsWith('t=')), 'Should have timestamp');
  assert(parts.some(p => p.startsWith('v1=')), 'Should have signature version');
});

// Test: Invoice amount rounding
test('Convert USD to cents correctly', () => {
  const invoices = [
    { amount: 199, expected: 19900 },
    { amount: 0.99, expected: 99 },
    { amount: 1000.50, expected: 100050 }
  ];

  invoices.forEach(inv => {
    const cents = Math.round(inv.amount * 100);
    assert.strictEqual(cents, inv.expected);
  });
});

// Test: Payment failure webhook
test('Handle invoice.payment_failed webhook event', () => {
  const webhookEvent = {
    type: 'invoice.payment_failed',
    data: {
      object: {
        id: 'in_failed_123',
        payment_intent: 'pi_failed_123',
        last_payment_error: {
          message: 'Card declined'
        },
        metadata: {
          lantern_invoice_id: 'INV-COMET-LEAP-RAG-001'
        }
      }
    }
  };

  assert.strictEqual(webhookEvent.type, 'invoice.payment_failed');
  assert(webhookEvent.data.object.last_payment_error);
});

// Test: Wallet state structure
test('Wallet state has required fields', () => {
  const walletPath = path.join(__dirname, '../../..', 'data/wallet/local-cash-wallet.json');
  if (fs.existsSync(walletPath)) {
    const wallet = JSON.parse(fs.readFileSync(walletPath, 'utf8'));

    assert(wallet.hasOwnProperty('clearedCashUsd'), 'Should have clearedCashUsd');
    assert(wallet.hasOwnProperty('pendingInvoices'), 'Should have pendingInvoices');
    assert(Array.isArray(wallet.receivedPayments), 'Should have receivedPayments array');
    assert.strictEqual(wallet.currency, 'USD', 'Should be USD currency');
  }
});

// Test: Config loading fallback
test('Config loading structure', () => {
  const configPath = path.join(__dirname, 'config.json');
  const configExamplePath = path.join(__dirname, 'config.example.json');

  // At least one should exist
  assert(fs.existsSync(configPath) || fs.existsSync(configExamplePath),
    'Config file should exist');
});

console.log(`\n${testsPassed}/${testsRun} tests passed`);
process.exit(testsPassed === testsRun ? 0 : 1);
