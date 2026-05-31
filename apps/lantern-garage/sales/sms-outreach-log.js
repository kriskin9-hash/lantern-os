/**
 * SMS Outreach Log
 *
 * Records SMS outreach events. Does not send messages.
 * SMS consent is enforced: no log entry is written without a matching consent record.
 */

const { files, appendJsonl, readJsonl, generateId, timestamp } = require("./sales-ledger");

function hasSmsConsent(leadId, phone) {
  const consents = readJsonl(files.smsConsent);
  return consents.some(
    (c) =>
      c.lead_id === leadId &&
      c.phone === phone &&
      c.consent_granted !== false
  );
}

async function recordSmsConsent(fields) {
  const required = ["lead_id", "phone", "consent_source", "consent_text"];
  const missing = required.filter((k) => !fields[k]);
  if (missing.length > 0) {
    throw new Error(`Missing required fields: ${missing.join(", ")}`);
  }

  const record = {
    consent_id: generateId("sms_consent"),
    lead_id: fields.lead_id,
    phone: fields.phone,
    consent_source: fields.consent_source,
    consent_text: fields.consent_text,
    consent_granted: fields.consent_granted !== false,
    timestamp: timestamp(),
  };

  await appendJsonl(files.smsConsent, record);

  const leads = readJsonl(files.leads);
  const lead = leads.filter((l) => l.lead_id === fields.lead_id).pop();
  if (lead) {
    const updated = {
      ...lead,
      phone: fields.phone,
      sms_consent_recorded: true,
      updated_at: timestamp(),
    };
    await appendJsonl(files.leads, updated);
  }

  return { ok: true, consent_id: record.consent_id, record };
}

async function logSmsOutreach(fields) {
  const required = ["lead_id", "phone", "message_preview"];
  const missing = required.filter((k) => !fields[k]);
  if (missing.length > 0) {
    throw new Error(`Missing required fields: ${missing.join(", ")}`);
  }

  if (!hasSmsConsent(fields.lead_id, fields.phone)) {
    throw new Error(
      `SMS consent not found for lead ${fields.lead_id} and phone ${fields.phone}. Record consent first.`
    );
  }

  const entry = {
    outreach_id: generateId("outreach"),
    lead_id: fields.lead_id,
    channel: "sms",
    phone: fields.phone,
    message_preview: fields.message_preview,
    sent_at: fields.sent_at || timestamp(),
    response_received: fields.response_received || false,
    response_preview: fields.response_preview || null,
    notes: fields.notes || null,
  };

  await appendJsonl(files.outreachLog, entry);
  return { ok: true, outreach_id: entry.outreach_id, entry };
}

function getSmsOutreachForLead(leadId) {
  const entries = readJsonl(files.outreachLog);
  return entries.filter((e) => e.lead_id === leadId && e.channel === "sms");
}

module.exports = {
  recordSmsConsent,
  logSmsOutreach,
  getSmsOutreachForLead,
  hasSmsConsent,
};
