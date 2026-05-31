# Billing Ledgers

This directory contains token usage and cost tracking for all fleet agents.

## Files

- `gemini-2.5-mini-001-ledger.jsonl` - Token usage log for Gemini 2.5 Mini agent slot

## Ledger Entry Format

Each line is a JSON object recording one agent task:

```json
{
  "timestamp": "2026-05-31T18:30:00Z",
  "slotId": "gemini-2.5-mini-agent-slot-001",
  "taskId": "task_001",
  "model": "gemini-2.5-mini",
  "inputTokens": 1250,
  "outputTokens": 890,
  "totalTokens": 2140,
  "estimatedCost": 0.00,
  "costTier": "free-tier",
  "taskDescription": "Generate convergence report",
  "status": "completed",
  "notes": "Within free tier limits"
}
```

## Billing Rules

1. **Free Tier Limit:** 5M tokens/month per agent
2. **Cost Tier Tracking:** Free tier vs. paid (if applicable)
3. **Monthly Reports:** Auto-generated in `reports/FLEET-BILLING-MONTHLY-YYYY-MM.md`
4. **Escalation:** Warning at 80% of monthly limit, operator approval required for overages

## Accountability

- **Operator:** Alex Place (approves budget changes, resolves overages)
- **Funder:** Courtney Blasioli (reviews monthly reports)
- **Tracking:** 100% transparent, every token logged
