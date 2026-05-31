# Ollama Agent Setup

**Status**: Ready
**Slot**: 38 (elastic pool)
**Model**: mistral (local)
**Cost**: $0 — runs entirely on operator hardware

---

## What It Does

Slot 38 is a local Ollama CLI agent for the Lantern OS fleet. It runs Mistral (or any pulled Ollama model) locally via the Ollama API at `localhost:11434`. Zero external API cost. Zero tokens. Zero network egress.

**Role**: Local inference worker for convergence, summarization, and low-latency tasks that don't require cloud models.

---

## Prerequisites

1. Install Ollama: https://ollama.com/download
2. Start Ollama: `ollama serve`
3. Pull a model: `ollama pull mistral` (already done — 4.4 GB)

---

## Usage

```powershell
# Send a prompt to local Mistral
.\scripts\Invoke-OllamaAgent.ps1 -Prompt "Summarize open issues"

# Check usage stats
.\scripts\Invoke-OllamaAgent.ps1 -ShowUsage

# Use a different model
.\scripts\Invoke-OllamaAgent.ps1 -Prompt "Your prompt" -Model llama3

# Pull a model if missing
.\scripts\Invoke-OllamaAgent.ps1 -PullModel -Model llama3

# Dry run (no API call)
.\scripts\Invoke-OllamaAgent.ps1 -Prompt "Test" -DryRun
```

---

## Bill Accountability

All usage logged to `data/ollama-usage.jsonl`:

```json
{"timestamp":"2026-05-31T15:00:00-04:00","model":"mistral","promptChars":150,"responseChars":300,"estimatedCostUsd":0.0}
```

Cost is always `$0` because inference runs locally. Logging exists for fleet accountability and hardware utilization tracking.

---

## Free Tier Limits

| Limit | Value |
|-------|-------|
| External cost | $0 |
| Latency | Determined by GPU/CPU |
| Privacy | 100% local |
| Credit card required | No |

---

## Files

| File | Purpose |
|------|---------|
| `scripts/Invoke-OllamaAgent.ps1` | CLI script |
| `data/ollama-usage.jsonl` | Usage log |
| `config/agents.json` | Slot 38 config |
| `config/agent-cli-registry.json` | CLI registry entry |

---

**End of Document**
