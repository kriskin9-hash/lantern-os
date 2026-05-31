/**
 * Discord Lead Intake
 *
 * Captures leads from Discord and stores them in the local sales ledger.
 * Does not send unsolicited SMS. Consent is recorded separately.
 */

const { files, appendJsonl, readJsonl, generateId, timestamp } = require("./sales-ledger");

async function captureDiscordLead(fields) {
  const required = ["discord_username", "problem_statement"];
  const missing = required.filter((k) => !fields[k]);
  if (missing.length > 0) {
    throw new Error(`Missing required fields: ${missing.join(", ")}`);
  }

  const lead = {
    lead_id: generateId("lead"),
    source: "discord",
    discord_username: fields.discord_username,
    discord_id: fields.discord_id || null,
    guild_id: fields.guild_id || null,
    channel_id: fields.channel_id || null,
    thread_id: fields.thread_id || null,
    problem_statement: fields.problem_statement,
    offer_interest: fields.offer_interest || null,
    urgency: fields.urgency || null,
    budget_signal: fields.budget_signal || null,
    gmail_contact: fields.gmail_contact || null,
    phone: fields.phone || null,
    sms_consent_recorded: false,
    status: "new",
    created_at: timestamp(),
    updated_at: timestamp(),
  };

  await appendJsonl(files.leads, lead);
  return { ok: true, lead_id: lead.lead_id, lead };
}

async function qualifyLead(leadId, qualification) {
  const leads = readJsonl(files.leads);
  const lead = leads.filter((l) => l.lead_id === leadId).pop();
  if (!lead) {
    throw new Error(`Lead not found: ${leadId}`);
  }

  const updated = {
    ...lead,
    status: qualification.status || lead.status,
    offer_interest: qualification.offer_interest || lead.offer_interest,
    urgency: qualification.urgency || lead.urgency,
    budget_signal: qualification.budget_signal || lead.budget_signal,
    gmail_contact: qualification.gmail_contact || lead.gmail_contact,
    phone: qualification.phone || lead.phone,
    qualification_notes: qualification.notes || null,
    updated_at: timestamp(),
  };

  await appendJsonl(files.leads, updated);
  return { ok: true, lead_id: leadId, lead: updated };
}

async function createOpportunity(fields) {
  const required = ["lead_id", "offer_name", "value_estimate"];
  const missing = required.filter((k) => !fields[k]);
  if (missing.length > 0) {
    throw new Error(`Missing required fields: ${missing.join(", ")}`);
  }

  const leads = readJsonl(files.leads);
  const lead = leads.filter((l) => l.lead_id === fields.lead_id).pop();
  if (!lead) {
    throw new Error(`Lead not found: ${fields.lead_id}`);
  }

  const opp = {
    opportunity_id: generateId("opp"),
    lead_id: fields.lead_id,
    offer_name: fields.offer_name,
    value_estimate: fields.value_estimate,
    stage: fields.stage || "discovery",
    expected_close_date: fields.expected_close_date || null,
    notes: fields.notes || null,
    payment_receipt_ids: [],
    created_at: timestamp(),
    updated_at: timestamp(),
  };

  await appendJsonl(files.opportunities, opp);

  const updatedLead = { ...lead, status: "opportunity", updated_at: timestamp() };
  await appendJsonl(files.leads, updatedLead);

  return { ok: true, opportunity_id: opp.opportunity_id, opportunity: opp };
}

module.exports = {
  captureDiscordLead,
  qualifyLead,
  createOpportunity,
};
