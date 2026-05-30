const fs = require('fs');
const path = require('path');

/**
 * Service Automation Framework for Lantern OS
 * Handles automated service delivery for existing offers
 */

class ServiceAutomator {
  constructor(repoRoot) {
    this.repoRoot = repoRoot || path.resolve(__dirname, '../../..');
    this.walletPath = path.join(this.repoRoot, 'data/wallet');
    this.ledgerPath = path.join(this.walletPath, 'ledger.jsonl');
    this.walletStatePath = path.join(this.walletPath, 'local-cash-wallet.json');
    this.invoicesPath = path.join(this.walletPath, 'invoices');
  }

  /**
   * Get existing service offers
   */
  getExistingOffers() {
    const walletState = this.readWalletState();
    return walletState?.existingOffersOnly || [];
  }

  /**
   * Read wallet state
   */
  readWalletState() {
    try {
      const content = fs.readFileSync(this.walletStatePath, 'utf8');
      return JSON.parse(content);
    } catch (error) {
      console.error('Failed to read wallet state:', error.message);
      return null;
    }
  }

  /**
   * Write wallet state
   */
  writeWalletState(state) {
    try {
      fs.writeFileSync(this.walletStatePath, JSON.stringify(state, null, 2));
      return true;
    } catch (error) {
      console.error('Failed to write wallet state:', error.message);
      return false;
    }
  }

  /**
   * Append to ledger
   */
  appendToLedger(entry) {
    try {
      const line = JSON.stringify(entry) + '\n';
      fs.appendFileSync(this.ledgerPath, line);
      return true;
    } catch (error) {
      console.error('Failed to append to ledger:', error.message);
      return false;
    }
  }

  /**
   * Create new service request
   */
  createServiceRequest(serviceOffer, customerData) {
    const requestId = `SRV-${Date.now()}`;
    const offer = this.getExistingOffers().find(o => o.includes(serviceOffer));
    
    if (!offer) {
      throw new Error(`Service offer not found: ${serviceOffer}`);
    }

    const pricing = this.getServicePricing(serviceOffer);
    
    const request = {
      requestId,
      serviceOffer: offer,
      customerEmail: customerData.email,
      customerName: customerData.name,
      amountUsd: pricing.amount,
      status: 'created',
      createdAt: new Date().toISOString(),
      assignedAgent: null,
      estimatedDelivery: this.getEstimatedDelivery(serviceOffer),
      requirements: customerData.requirements || []
    };

    this.appendToLedger({
      event: 'service_request_created',
      requestId,
      serviceOffer: offer,
      customerEmail: customerData.email,
      amountUsd: pricing.amount,
      timestamp: new Date().toISOString()
    });

    return request;
  }

  /**
   * Get service pricing
   */
  getServicePricing(serviceOffer) {
    const pricingMap = {
      'COMET LEAP Founder Report Pack': { amount: 299, deliveryDays: 7 },
      'Local RAG / Repo Cleanup Sprint': { amount: 199, deliveryDays: 5 },
      'Windows / Lantern Setup Session': { amount: 149, deliveryDays: 3 },
      'Parent / Homeschool Creative Learning Packet': { amount: 99, deliveryDays: 4 },
      'Small-Business AI Cleanup and Training Session': { amount: 249, deliveryDays: 6 }
    };

    for (const [key, value] of Object.entries(pricingMap)) {
      if (serviceOffer.includes(key) || key.includes(serviceOffer)) {
        return value;
      }
    }

    return { amount: 199, deliveryDays: 5 }; // Default pricing
  }

  /**
   * Get estimated delivery time
   */
  getEstimatedDelivery(serviceOffer) {
    const pricing = this.getServicePricing(serviceOffer);
    const deliveryDate = new Date();
    deliveryDate.setDate(deliveryDate.getDate() + pricing.deliveryDays);
    return deliveryDate.toISOString();
  }

  /**
   * Assign agent to service request
   */
  assignAgent(requestId, agentId) {
    this.appendToLedger({
      event: 'agent_assigned',
      requestId,
      agentId,
      timestamp: new Date().toISOString()
    });

    return { success: true, requestId, agentId };
  }

  /**
   * Generate invoice for completed service
   */
  generateInvoice(requestId) {
    const invoiceId = `INV-${requestId}`;
    const invoicePath = path.join(this.invoicesPath, `${invoiceId}.md`);
    
    // Find the service request from ledger
    const ledger = this.readLedger();
    const serviceRequest = ledger.find(entry => 
      entry.event === 'service_request_created' && entry.requestId === requestId
    );

    if (!serviceRequest) {
      throw new Error('Service request not found');
    }

    const invoiceContent = `# Invoice: ${invoiceId}
Customer Email: ${serviceRequest.customerEmail}
Customer Name: ${serviceRequest.customerName}
Date: ${new Date().toISOString().split('T')[0]}
Due Date: ${new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]}

## Service Details
Service: ${serviceRequest.serviceOffer}
Request ID: ${serviceRequest.requestId}

## Amount Due
Total: $${serviceRequest.amountUsd} USD

## Payment Terms
Payment is due within 7 days of invoice date.
Services rendered as per Lantern OS service agreement.

---
Generated by Lantern OS Automated System
`;

    // Ensure invoices directory exists
    if (!fs.existsSync(this.invoicesPath)) {
      fs.mkdirSync(this.invoicesPath, { recursive: true });
    }

    fs.writeFileSync(invoicePath, invoiceContent);

    // Update wallet state
    const walletState = this.readWalletState();
    if (walletState) {
      walletState.pendingInvoices = walletState.pendingInvoices || [];
      walletState.pendingInvoices.push({
        invoiceId,
        offer: serviceRequest.serviceOffer,
        amountUsd: serviceRequest.amountUsd,
        status: 'sent',
        invoicePath: `data/wallet/invoices/${invoiceId}.md`,
        customerEmail: serviceRequest.customerEmail
      });
      walletState.draftInvoiceUsd = (walletState.draftInvoiceUsd || 0) + serviceRequest.amountUsd;
      this.writeWalletState(walletState);
    }

    this.appendToLedger({
      event: 'invoice_generated',
      invoiceId,
      requestId,
      amountUsd: serviceRequest.amountUsd,
      customerEmail: serviceRequest.customerEmail,
      timestamp: new Date().toISOString()
    });

    return { invoiceId, invoicePath, amountUsd: serviceRequest.amountUsd };
  }

  /**
   * Read ledger
   */
  readLedger(limit = 100) {
    try {
      const content = fs.readFileSync(this.ledgerPath, 'utf8');
      return content.split('\n')
        .filter(line => line.trim())
        .slice(-limit)
        .map(line => JSON.parse(line));
    } catch (error) {
      console.error('Failed to read ledger:', error.message);
      return [];
    }
  }

  /**
   * Get active service requests
   */
  getActiveServiceRequests() {
    const ledger = this.readLedger(50);
    const activeRequests = new Map();

    ledger.forEach(entry => {
      if (entry.event === 'service_request_created') {
        activeRequests.set(entry.requestId, entry);
      } else if (entry.event === 'service_completed') {
        activeRequests.delete(entry.requestId);
      }
    });

    return Array.from(activeRequests.values());
  }

  /**
   * Mark service as completed
   */
  completeService(requestId, deliveryArtifacts = []) {
    this.appendToLedger({
      event: 'service_completed',
      requestId,
      deliveryArtifacts,
      timestamp: new Date().toISOString()
    });

    return { success: true, requestId };
  }
}

module.exports = ServiceAutomator;