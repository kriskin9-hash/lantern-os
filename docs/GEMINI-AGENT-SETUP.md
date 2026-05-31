# Gemini Agent Setup

**Status**: Ready pending key  
**Slot**: 37 (elastic pool)  
**Model**: gemini-1.5-flash (cheapest) or gemini-2.5-flash-preview  
**Cost**: Free tier — no credit card required  

---

## What It Does

Slot 37 is a bill-accountable Gemini CLI agent for the Lantern OS fleet. It runs on Google AI Studio's free tier and logs every token for cost tracking.

**Role**: Cheap inference worker for branches/PRs/issues convergence tasks.

---

## Get Free API Key (5 minutes)

1. Go to https://aistudio.google.com/app/apikey
2. Sign in with Google account
3. Click "Create API Key"
4. Copy the key

## Configure

```powershell
$env:GEMINI_API_KEY = "your-key-here"
```

Or set permanently:
```powershell
[Environment]::SetEnvironmentVariable("GEMINI_API_KEY", "your-key-here", "User")
```

---

## Free Tier Limits

| Limit | Value |
|-------|-------|
| Requests per minute | 60 |
| Requests per day | 1,000 |
| Cost | $0 |
| Credit card required | No |

---

## Usage

```powershell
# Send a prompt
.\scripts\Invoke-GeminiAgent.ps1 -Prompt "Summarize open issues"

# Check usage stats
.\scripts\Invoke-GeminiAgent.ps1 -ShowUsage

# Use cheapest model (default)
.\scripts\Invoke-GeminiAgent.ps1 -Prompt "Your prompt" -Model gemini-1.5-flash

# Dry run (no API call)
.\scripts\Invoke-GeminiAgent.ps1 -Prompt "Test" -DryRun
```

---

## Bill Accountability

All usage logged to `data/gemini-usage.jsonl`:

```json
{"timestamp":"2026-05-31T14:00:00-04:00","model":"gemini-1.5-flash","inputTokens":150,"outputTokens":300,"estimatedCostUsd":0.000101}
```

Even on free tier, cost is estimated so you know what you would pay if you upgraded.

---

## Files

| File | Purpose |
|------|---------|
| `scripts/Invoke-GeminiAgent.ps1` | CLI script |
| `data/gemini-usage.jsonl` | Usage log |
| `config/agents.json` | Slot 37 config |
| `config/agent-cli-registry.json` | CLI registry entry |

---

**End of Document**
