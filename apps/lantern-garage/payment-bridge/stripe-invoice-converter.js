const fs = require('fs');
const path = require('path');

/**
 * Convert Lantern invoice format to Stripe invoice format
 */
function convertLanternInvoiceToStripe(invoicePath) {
  const repoRoot = path.resolve(__dirname, '../../..');
  const fullInvoicePath = path.join(repoRoot, invoicePath);
  
  if (!fs.existsSync(fullInvoicePath)) {
    throw new Error(`Invoice file not found: ${fullInvoicePath}`);
  }
  
  const invoiceContent = fs.readFileSync(fullInvoicePath, 'utf8');
  const invoiceData = parseLanternInvoice(invoiceContent);
  
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
      generated_by: 'lantern-os',
      invoice_path: invoicePath
    }
  };
  
  return stripeInvoice;
}

/**
 * Parse Lantern invoice markdown format
 */
function parseLanternInvoice(markdown) {
  const lines = markdown.split('\n');
  const invoiceData = {
    invoiceId: '',
    customerEmail: '',
    description: '',
    dueDate: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000), // Default 7 days
    lineItems: [],
    offer: ''
  };
  
  lines.forEach(line => {
    const trimmed = line.trim();
    if (trimmed.startsWith('# Invoice:')) {
      invoiceData.invoiceId = trimmed.replace('# Invoice:', '').trim();
    } else if (trimmed.startsWith('Customer Email:')) {
      invoiceData.customerEmail = trimmed.replace('Customer Email:', '').trim();
    } else if (trimmed.startsWith('Description:')) {
      invoiceData.description = trimmed.replace('Description:', '').trim();
    } else if (trimmed.startsWith('Due Date:')) {
      invoiceData.dueDate = new Date(trimmed.replace('Due Date:', '').trim());
    } else if (trimmed.startsWith('Offer:')) {
      invoiceData.offer = trimmed.replace('Offer:', '').trim();
    } else if (trimmed.startsWith('- ')) {
      // Parse line items
      const itemText = trimmed.replace('- ', '').trim();
      const amountMatch = itemText.match(/\$(\d+)/);
      if (amountMatch) {
        invoiceData.lineItems.push({
          description: itemText.replace(/\$\d+/, '').trim(),
          amount: parseInt(amountMatch[1]),
          quantity: 1
        });
      }
    }
  });
  
  // Set default description if not found
  if (!invoiceData.description && invoiceData.offer) {
    invoiceData.description = invoiceData.offer;
  }
  
  return invoiceData;
}

/**
 * Generate Stripe invoice from wallet invoice data
 */
function generateStripeInvoiceFromWallet(walletInvoice) {
  const stripeInvoice = {
    customer: walletInvoice.customerEmail || 'placeholder@example.com',
    description: walletInvoice.offer || 'Lantern OS Service',
    currency: 'usd',
    items: [{
      amount: Math.round(walletInvoice.amountUsd * 100),
      currency: 'usd',
      description: walletInvoice.offer || 'Service',
      quantity: 1
    }],
    due_date: Math.floor(new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).getTime() / 1000),
    metadata: {
      lantern_invoice_id: walletInvoice.invoiceId,
      lantern_offer: walletInvoice.offer,
      generated_by: 'lantern-os'
    }
  };
  
  return stripeInvoice;
}

module.exports = {
  convertLanternInvoiceToStripe,
  parseLanternInvoice,
  generateStripeInvoiceFromWallet
};