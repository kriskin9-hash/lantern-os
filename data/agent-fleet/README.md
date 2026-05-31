# Agent Fleet Configuration

This directory contains agent slot configurations for the Lantern OS fleet.

## Current Slots

### Gemini 2.5 Mini (Agent Slot 001)
**File:** `slots/gemini-2.5-mini-agent-slot-001.json`

- **Model:** Gemini 2.5 Mini (Google)
- **Cost:** Free tier ($0/month)
- **Status:** Awaiting green light
- **Billing:** `data/billing/gemini-2.5-mini-001-ledger.jsonl`

## Green Light Checklist

Before starting the fleet:

- [ ] Create Gemini API key at https://aistudio.google.com/app/apikey
- [ ] Save GEMINI_API_KEY to `.env.local` (do NOT commit)
- [ ] Test API key with `scripts/Start-FleetWithGemini.ps1`
- [ ] Verify billing ledger file exists
- [ ] All branches merged to master
- [ ] Tests pass (417+ pass expected)
- [ ] Operator approval given by Alex Place

## Startup

```powershell
# On your Windows machine:
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Start-FleetWithGemini.ps1 `
  -SlotId "gemini-2.5-mini-agent-slot-001" `
  -MaxConcurrentTasks 3
```

## Billing Accountability

Every token is logged. Monthly reports generated in `reports/FLEET-BILLING-MONTHLY-*.md`.

**Cost discipline enforced:** Free tier only. Operator approval required for any paid upgrades.
