/**
 * Sales MCP Tools
 *
 * Exposes the local sales ledger as MCP-style JSON-RPC tools.
 * These are plain functions; the caller is responsible for transport.
 *
 * Tools:
 *   capture_discord_lead
 *   qualify_lead
 *   create_opportunity
 *   log_gmail_outreach
 *   log_sms_outreach
 *   record_sms_consent
 *   attach_payment_receipt
 *   next_best_sales_action
 *   summarize_sales_pipeline
 */

const {
  captureDiscordLead,
  qualifyLead,
  createOpportunity,
} = require("./discord-lead-intake");

const {
  logGmailOutreach,
  getOutreachForLead,
  getPendingFollowUps,
} = require("./gmail-outreach-log");

const {
  recordSmsConsent,
  logSmsOutreach,
  hasSmsConsent,
} = require("./sms-outreach-log");

const {
  attachPaymentReceipt,
} = require("./payment-receipts");

const { files, readJsonl, timestamp } = require("./sales-ledger");

const TOOLS = {
  capture_discord_lead: {
    description: "Create a lead from Discord intake.",
    parameters: {
      discord_username: { type: "string", required: true },
      discord_id: { type: "string", required: false },
      guild_id: { type: "string", required: false },
      channel_id: { type: "string", required: false },
      thread_id: { type: "string", required: false },
      problem_statement: { type: "string", required: true },
      offer_interest: { type: "string", required: false },
      urgency: { type: "string", required: false },
      budget_signal: { type: "string", required: false },
      gmail_contact: { type: "string", required: false },
      phone: { type: "string", required: false },
    },
    handler: captureDiscordLead,
  },

  qualify_lead: {
    description: "Update lead qualification fields.",
    parameters: {
      lead_id: { type: "string", required: true },
      status: { type: "string", required: false },
      offer_interest: { type: "string", required: false },
      urgency: { type: "string", required: false },
      budget_signal: { type: "string", required: false },
      gmail_contact: { type: "string", required: false },
      phone: { type: "string", required: false },
      notes: { type: "string", required: false },
    },
    handler: async (fields) => qualifyLead(fields.lead_id, fields),
  },

  create_opportunity: {
    description: "Promote a lead to an opportunity.",
    parameters: {
      lead_id: { type: "string", required: true },
      offer_name: { type: "string", required: true },
      value_estimate: { type: "number", required: true },
      stage: { type: "string", required: false },
      expected_close_date: { type: "string", required: false },
      notes: { type: "string", required: false },
    },
    handler: createOpportunity,
  },

  log_gmail_outreach: {
    description: "Log a Gmail outreach event.",
    parameters: {
      lead_id: { type: "string", required: true },
      to_address: { type: "string", required: false },
      subject: { type: "string", required: true },
      body_preview: { type: "string", required: true },
      sent_at: { type: "string", required: false },
      response_received: { type: "boolean", required: false },
      response_preview: { type: "string", required: false },
      follow_up_scheduled_at: { type: "string", required: false },
      notes: { type: "string", required: false },
    },
    handler: logGmailOutreach,
  },

  record_sms_consent: {
    description: "Record explicit SMS consent before any SMS outreach.",
    parameters: {
      lead_id: { type: "string", required: true },
      phone: { type: "string", required: true },
      consent_source: { type: "string", required: true },
      consent_text: { type: "string", required: true },
      consent_granted: { type: "boolean", required: false },
    },
    handler: recordSmsConsent,
  },

  log_sms_outreach: {
    description: "Log an SMS outreach event. Requires prior consent.",
    parameters: {
      lead_id: { type: "string", required: true },
      phone: { type: "string", required: true },
      message_preview: { type: "string", required: true },
      sent_at: { type: "string", required: false },
      response_received: { type: "boolean", required: false },
      response_preview: { type: "string", required: false },
      notes: { type: "string", required: false },
    },
    handler: logSmsOutreach,
  },

  attach_payment_receipt: {
    description: "Attach a payment receipt to an opportunity.",
    parameters: {
      opportunity_id: { type: "string", required: true },
      amount: { type: "number", required: true },
      currency: { type: "string", required: true },
      payment_method: { type: "string", required: true },
      reference: { type: "string", required: false },
      received_at: { type: "string", required: false },
      notes: { type: "string", required: false },
    },
    handler: attachPaymentReceipt,
  },

  next_best_sales_action: {
    description: "Recommend the next action for a lead or opportunity.",
    parameters: {
      lead_id: { type: "string", required: true },
    },
    handler: async (fields) => {
      const leads = readJsonl(files.leads);
      const lead = leads.filter((l) => l.lead_id === fields.lead_id).pop();
      if (!lead) throw new Error(`Lead not found: ${fields.lead_id}`);

      const opps = readJsonl(files.opportunities);
      const opp = opps.filter((o) => o.lead_id === fields.lead_id).pop();
      const outreach = readJsonl(files.outreachLog).filter(
        (e) => e.lead_id === fields.lead_id
      );
      const consents = readJsonl(files.smsConsent).filter(
        (c) => c.lead_id === fields.lead_id
      );

      const lastGmail = outreach
        .filter((e) => e.channel === "gmail")
        .pop();
      const lastSms = outreach
        .filter((e) => e.channel === "sms")
        .pop();

      let action = "Qualify further via Gmail: send context, preview link, or quote.";
      if (lead.status === "new") {
        action = "Send Gmail introduction with problem confirmation and offer preview.";
      } else if (lead.status === "qualified" && !consents.length) {
        action = "Ask for email or phone consent in Discord; then send Gmail follow-up.";
      } else if (lead.status === "qualified" && consents.length && !lastSms) {
        action = "Send first SMS nudge: 'Want the preview link?'";
      } else if (opp && opp.stage === "discovery") {
        action = "Send Gmail proposal/quote and schedule close call.";
      } else if (opp && opp.stage === "proposal") {
        action = "SMS close nudge: 'Want me to reserve a slot?' or 'I sent the invoice.'";
      } else if (opp && opp.stage === "closed_won") {
        action = "Customer onboarding: send welcome Gmail and schedule delivery.";
      }

      return {
        ok: true,
        lead_id: fields.lead_id,
        action,
        context: {
          lead_status: lead.status,
          has_opportunity: !!opp,
          opportunity_stage: opp ? opp.stage : null,
          gmail_count: outreach.filter((e) => e.channel === "gmail").length,
          sms_count: outreach.filter((e) => e.channel === "sms").length,
          has_sms_consent: consents.length > 0,
          last_gmail_subject: lastGmail ? lastGmail.subject : null,
          last_sms_preview: lastSms ? lastSms.message_preview : null,
        },
      };
    },
  },

  summarize_sales_pipeline: {
    description: "Return a lightweight pipeline summary from the local ledger.",
    parameters: {},
    handler: async () => {
      const leads = readJsonl(files.leads);
      const opps = readJsonl(files.opportunities);
      const outreach = readJsonl(files.outreachLog);
      const receipts = readJsonl(files.paymentReceipts);

      const latestLeadStatus = new Map();
      for (const l of leads) {
        latestLeadStatus.set(l.lead_id, l.status);
      }

      const newLeads = leads.filter((l) => l.status === "new").length;
      const qualifiedLeads = leads.filter((l) => l.status === "qualified").length;
      const opportunityLeads = leads.filter((l) => l.status === "opportunity").length;
      const customers = leads.filter((l) => l.status === "customer").length;

      const totalPipelineValue = opps
        .filter((o) => o.stage !== "closed_won" && o.stage !== "closed_lost")
        .reduce((sum, o) => sum + (Number(o.value_estimate) || 0), 0);

      const wonValue = receipts.reduce(
        (sum, r) => sum + (Number(r.amount) || 0),
        0
      );

      return {
        ok: true,
        generated_at: timestamp(),
        counts: {
          total_leads: latestLeadStatus.size,
          new: newLeads,
          qualified: qualifiedLeads,
          opportunity: opportunityLeads,
          customer: customers,
          opportunities: opps.length,
          gmail_outreach: outreach.filter((e) => e.channel === "gmail").length,
          sms_outreach: outreach.filter((e) => e.channel === "sms").length,
          payment_receipts: receipts.length,
        },
        value: {
          total_pipeline_estimate: totalPipelineValue,
          total_won_revenue: wonValue,
          currency: "USD",
        },
        stages: {
          discovery: opps.filter((o) => o.stage === "discovery").length,
          proposal: opps.filter((o) => o.stage === "proposal").length,
          closed_won: opps.filter((o) => o.stage === "closed_won").length,
          closed_lost: opps.filter((o) => o.stage === "closed_lost").length,
        },
      };
    },
  },
};

/**
 * Invoke a tool by name with a flat parameters object.
 * Returns a Promise resolving to the tool result.
 */
async function invokeTool(name, params = {}) {
  const tool = TOOLS[name];
  if (!tool) throw new Error(`Unknown tool: ${name}`);

  const provided = Object.keys(params || {});
  const missing = Object.entries(tool.parameters)
    .filter(([_, spec]) => spec.required)
    .filter(([key]) => !provided.includes(key))
    .map(([key]) => key);

  if (missing.length > 0) {
    throw new Error(`Missing required parameters for ${name}: ${missing.join(", ")}`);
  }

  return tool.handler(params);
}

/**
 * Return a JSON-RPC-style tool descriptor list for MCP discovery.
 */
function listTools() {
  return Object.entries(TOOLS).map(([name, spec]) => ({
    name,
    description: spec.description,
    parameters: spec.parameters,
  }));
}

module.exports = {
  TOOLS,
  invokeTool,
  listTools,
};
