<#
.SYNOPSIS
    Validate Lantern Garage sales MCP tools locally.
.DESCRIPTION
    Runs the sales tool module through Node.js directly to verify each tool
    without requiring the garage server to be online.
#>
$ErrorActionPreference = "Stop"
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$salesDir = Join-Path (Join-Path (Join-Path $repoRoot "apps") "lantern-garage") "sales"
$testScript = @"
const { invokeTool, listTools } = require('./sales-mcp-tools');

async function run() {
  const results = [];

  // 1. List tools
  const tools = listTools();
  results.push({ step: 'list_tools', ok: tools.length === 9, count: tools.length });

  // 2. Capture Discord lead
  const lead = await invokeTool('capture_discord_lead', {
    discord_username: 'test_user',
    discord_id: '123456',
    guild_id: 'guild_1',
    channel_id: 'chan_1',
    problem_statement: 'Need a local-first agent OS for my lab.',
    offer_interest: 'Lantern Garage founding seat',
    urgency: 'high',
    budget_signal: '$500-1000',
    gmail_contact: 'test@example.com'
  });
  results.push({ step: 'capture_discord_lead', ok: lead.ok && lead.lead_id, lead_id: lead.lead_id });
  const leadId = lead.lead_id;

  // 3. Qualify lead
  const qualified = await invokeTool('qualify_lead', {
    lead_id: leadId,
    status: 'qualified',
    notes: 'Confirmed budget and timeline.'
  });
  results.push({ step: 'qualify_lead', ok: qualified.ok && qualified.lead.status === 'qualified', status: qualified.lead.status });

  // 4. Create opportunity
  const opp = await invokeTool('create_opportunity', {
    lead_id: leadId,
    offer_name: 'Lantern Garage Founding Seat',
    value_estimate: 750,
    stage: 'discovery',
    notes: 'Wants demo next week.'
  });
  results.push({ step: 'create_opportunity', ok: opp.ok && opp.opportunity_id, opp_id: opp.opportunity_id });
  const oppId = opp.opportunity_id;

  // 5. Log Gmail outreach
  const gmail = await invokeTool('log_gmail_outreach', {
    lead_id: leadId,
    subject: 'Lantern Garage Preview + Quote',
    body_preview: 'Here is the preview link and quote you requested...',
    to_address: 'test@example.com'
  });
  results.push({ step: 'log_gmail_outreach', ok: gmail.ok, outreach_id: gmail.outreach_id });

  // 6. Record SMS consent
  const consent = await invokeTool('record_sms_consent', {
    lead_id: leadId,
    phone: '+15551234567',
    consent_source: 'discord',
    consent_text: 'User asked to receive SMS follow-up/payment link',
    consent_granted: true
  });
  results.push({ step: 'record_sms_consent', ok: consent.ok, consent_id: consent.consent_id });

  // 7. Log SMS outreach
  const sms = await invokeTool('log_sms_outreach', {
    lead_id: leadId,
    phone: '+15551234567',
    message_preview: 'Want the preview link?'
  });
  results.push({ step: 'log_sms_outreach', ok: sms.ok, outreach_id: sms.outreach_id });

  // 8. Attach payment receipt
  const receipt = await invokeTool('attach_payment_receipt', {
    opportunity_id: oppId,
    amount: 750,
    currency: 'USD',
    payment_method: 'stripe',
    reference: 'pi_test_123'
  });
  results.push({ step: 'attach_payment_receipt', ok: receipt.ok, receipt_id: receipt.receipt_id, opp_stage: receipt.opportunity.stage });

  // 9. Next best action (customer)
  const action = await invokeTool('next_best_sales_action', { lead_id: leadId });
  results.push({ step: 'next_best_sales_action', ok: action.ok && action.action.includes('onboarding'), action: action.action });

  // 10. Pipeline summary
  const pipeline = await invokeTool('summarize_sales_pipeline', {});
  results.push({ step: 'summarize_sales_pipeline', ok: pipeline.ok && pipeline.counts.customer >= 1, customers: pipeline.counts.customer });

  // 11. SMS consent guardrail
  try {
    await invokeTool('log_sms_outreach', { lead_id: leadId, phone: '+15559999999', message_preview: 'Should fail' });
    results.push({ step: 'sms_guardrail', ok: false, error: 'Expected error for missing consent' });
  } catch (err) {
    results.push({ step: 'sms_guardrail', ok: err.message.includes('consent'), error: err.message });
  }

  const passed = results.filter(r => r.ok).length;
  const failed = results.filter(r => !r.ok).length;
  console.log(JSON.stringify({ passed, failed, total: results.length, results }, null, 2));
  process.exit(failed > 0 ? 1 : 0);
}

run().catch(e => { console.error(e.message); process.exit(1); });
"@

Push-Location $salesDir
try {
    $tempFile = Join-Path $salesDir ([System.IO.Path]::GetRandomFileName() + ".js")
    $testScript | Set-Content -Path $tempFile -Encoding UTF8
    & node $tempFile
    if ($LASTEXITCODE -ne 0) { throw "Sales MCP tool tests failed with exit code $LASTEXITCODE" }
}
finally {
    if (Test-Path $tempFile) { Remove-Item $tempFile -Force }
    Pop-Location
}
