/**
 * Payment Receipts
 *
 * Attaches payment receipts to opportunities.
 * Does not process payments; it records evidence of payment.
 */

const { files, appendJsonl, readJsonl, generateId, timestamp } = require("./sales-ledger");

async function attachPaymentReceipt(fields) {
  const required = ["opportunity_id", "amount", "currency", "payment_method"];
  const missing = required.filter((k) => !fields[k]);
  if (missing.length > 0) {
    throw new Error(`Missing required fields: ${missing.join(", ")}`);
  }

  const opps = readJsonl(files.opportunities);
  const opp = opps.filter((o) => o.opportunity_id === fields.opportunity_id).pop();
  if (!opp) {
    throw new Error(`Opportunity not found: ${fields.opportunity_id}`);
  }

  const receipt = {
    receipt_id: generateId("receipt"),
    opportunity_id: fields.opportunity_id,
    lead_id: opp.lead_id,
    amount: fields.amount,
    currency: fields.currency,
    payment_method: fields.payment_method,
    reference: fields.reference || null,
    received_at: fields.received_at || timestamp(),
    notes: fields.notes || null,
  };

  await appendJsonl(files.paymentReceipts, receipt);

  const updatedOpp = {
    ...opp,
    payment_receipt_ids: [...opp.payment_receipt_ids, receipt.receipt_id],
    stage: "closed_won",
    updated_at: timestamp(),
  };
  await appendJsonl(files.opportunities, updatedOpp);

  const leads = readJsonl(files.leads);
  const lead = leads.filter((l) => l.lead_id === opp.lead_id).pop();
  if (lead) {
    const updatedLead = { ...lead, status: "customer", updated_at: timestamp() };
    await appendJsonl(files.leads, updatedLead);
  }

  return { ok: true, receipt_id: receipt.receipt_id, receipt, opportunity: updatedOpp };
}

function getReceiptsForOpportunity(opportunityId) {
  const receipts = readJsonl(files.paymentReceipts);
  return receipts.filter((r) => r.opportunity_id === opportunityId);
}

module.exports = {
  attachPaymentReceipt,
  getReceiptsForOpportunity,
};
