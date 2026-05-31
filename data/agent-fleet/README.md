# Agent Fleet Configuration

This directory contains agent slot configurations for the Lantern OS fleet orchestration system.

## Active Slots

### Slot 001: Gemini 2.5 Mini (Free Tier)
**File:** `slots/gemini-2.5-mini-agent-slot-001.json`

- **Model:** Gemini 2.5 Mini (Google)
- **Cost:** Free tier ($0/month)
- **Rate Limit:** 15K requests/min, 5M tokens/month
- **Status:** Awaiting green light
- **Best For:** Lightweight tasks, report generation, documentation
- **Billing:** `data/billing/gemini-2.5-mini-001-ledger.jsonl`

### Slot 002: Gemini 2.5 Flash (Free Tier)
**File:** `slots/gemini-2.5-flash-agent-slot-002.json`

- **Model:** Gemini 2.5 Flash (Google)
- **Cost:** Free tier ($0/month)
- **Rate Limit:** 15K requests/min, 5M tokens/month
- **Status:** Awaiting green light
- **Best For:** Real-time tasks, streaming, quick decisions
- **Differentiator:** Faster token generation than Mini
- **Billing:** `data/billing/gemini-2.5-flash-002-ledger.jsonl`

### Slot 003: Groq Llama 4 Scout (Free Tier)
**File:** `slots/groq-llama4-scout-agent-slot-003.json`

- **Model:** Llama 4 Scout 8B (Groq LPU)
- **Cost:** Free tier ($0/month)
- **Rate Limit:** 14.4K requests/min, 10M tokens/month
- **Status:** Awaiting green light
- **Best For:** Low-latency code generation, real-time reasoning
- **Differentiator:** 500+ tokens/sec throughput via Groq LPU hardware
- **Billing:** `data/billing/groq-llama-scout-003-ledger.jsonl`

### Slot 004: DeepSeek V3 (Freemium)
**File:** `slots/deepseek-v3-agent-slot-004.json`

- **Model:** DeepSeek Chat V3
- **Cost:** Free tier (5M tokens), then $0.28/$0.56 per 1M tokens
- **Rate Limit:** 3K requests/min
- **Status:** Awaiting green light
- **Best For:** Technical writing, system design, reasoning-heavy tasks
- **Monthly Budget:** $100 (after free tier)
- **Billing:** `data/billing/deepseek-v3-004-ledger.jsonl`

## Green Light Checklist (Per Slot)

Before starting a fleet slot:

- [ ] Create API key at provider's console
- [ ] Save API key to `.env.local` (do NOT commit)
- [ ] Test API key with `scripts/Test-FleetSlot-[Provider].ps1`
- [ ] Verify billing ledger file exists and is empty
- [ ] All tests pass (452+ pytest expected)
- [ ] Operator approval given

## Startup (All Slots)

```powershell
# Start entire fleet with all active slots
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Start-LanternFleetFull.ps1 `
  -Slots "gemini-2.5-mini-agent-slot-001","gemini-2.5-flash-agent-slot-002","groq-llama4-scout-agent-slot-003","deepseek-v3-agent-slot-004" `
  -MaxConcurrentTasks 5
```

## Billing Accountability

Every token across all slots is logged in parallel ledger files:
- Gemini Mini: `data/billing/gemini-2.5-mini-001-ledger.jsonl`
- Gemini Flash: `data/billing/gemini-2.5-flash-002-ledger.jsonl`
- Groq Llama: `data/billing/groq-llama-scout-003-ledger.jsonl`
- DeepSeek: `data/billing/deepseek-v3-004-ledger.jsonl`

Monthly reports generated in `reports/FLEET-BILLING-MONTHLY-*.md`.

**Cost discipline:** Free tiers only until operator approves paid slots (currently DeepSeek slot 004).

## API Keys Required

| Provider | Env Var | Get Key | Cost |
|----------|---------|---------|------|
| Google Gemini | `GEMINI_API_KEY` | https://aistudio.google.com/app/apikey | Free |
| Groq | `GROQ_API_KEY` | https://console.groq.com/keys | Free |
| DeepSeek | `DEEPSEEK_API_KEY` | https://platform.deepseek.com/api_keys | Freemium |

## Fleet Health Monitoring

```powershell
# Check all slot health
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Get-LanternFleetHealth.ps1
```

Expected output:
- Slot 001 (Gemini Mini): ✓ Ready / ○ Offline
- Slot 002 (Gemini Flash): ✓ Ready / ○ Offline
- Slot 003 (Groq Llama): ✓ Ready / ○ Offline
- Slot 004 (DeepSeek): ✓ Ready / ○ Offline

## Concurrent Execution Strategy

Slots are designed to run in parallel:
- Slots 001 & 002: Share Gemini API key (same provider, different models)
- Slot 003: Independent Groq infrastructure
- Slot 004: Independent DeepSeek infrastructure

Max concurrent tasks: 5 (1 per slot + 1 dispatcher)
