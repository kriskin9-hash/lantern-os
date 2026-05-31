/**
 * Gmail Outreach Log
 *
 * Records Gmail-based outreach events against leads/opportunities.
 * This module logs only; it does not send email.
 */

const { files, appendJsonl, readJsonl, generateId, timestamp } = require("./sales-ledger");

async function logGmailOutreach(fields) {
  const required = ["lead_id", "subject", "body_preview"];
  const missing = required.filter((k) => !fields[k]);
  if (missing.length > 0) {
    throw new Error(`Missing required fields: ${missing.join(", ")}`);
  }

  const entry = {
    outreach_id: generateId("outreach"),
    lead_id: fields.lead_id,
    channel: "gmail",
    to_address: fields.to_address || null,
    subject: fields.subject,
    body_preview: fields.body_preview,
    sent_at: fields.sent_at || timestamp(),
    response_received: fields.response_received || false,
    response_preview: fields.response_preview || null,
    follow_up_scheduled_at: fields.follow_up_scheduled_at || null,
    notes: fields.notes || null,
  };

  await appendJsonl(files.outreachLog, entry);
  return { ok: true, outreach_id: entry.outreach_id, entry };
}

function getOutreachForLead(leadId) {
  const entries = readJsonl(files.outreachLog);
  return entries.filter((e) => e.lead_id === leadId);
}

function getPendingFollowUps() {
  const entries = readJsonl(files.outreachLog);
  const now = timestamp();
  return entries.filter(
    (e) =>
      e.channel === "gmail" &&
      !e.response_received &&
      e.follow_up_scheduled_at &&
      e.follow_up_scheduled_at <= now
  );
}

module.exports = {
  logGmailOutreach,
  getOutreachForLead,
  getPendingFollowUps,
};
