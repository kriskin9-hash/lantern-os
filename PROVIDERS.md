# Lantern OS — AI Provider Chain Documentation

**Complete inventory of all 10 LLM providers, their configuration, and current status.**

---

## Configuration Overview

| Component | Location | Purpose |
|-----------|----------|---------|
| **Provider Registry** | `data/pcsf/provider.pcsf.json` | Declared providers, fallback order, default models |
| **Settings Manifest** | `data/pcsf/settings.pcsf.json` | Environment variables, state (present/absent), API key URLs |
| **Environment Template** | `.env.example` | Local copy with instructions |
| **Live Configuration** | `.env` (git-ignored) | User's actual API keys and settings |
| **Server Loader** | `apps/lantern-garage/server.js` | Reads .env at startup (regex `^[A-Z0-9_]+`) |
| **Hot Reload API** | `POST /api/settings/providers` | Change provider keys without restart |

---

## The 10 Providers

### ACTIVE (Recommended for Production)

#### 1. **Anthropic Claude** ✅
- **API Key:** `ANTHROPIC_API_KEY` (format: `sk-ant-...`)
- **Model Var:** `ANTHROPIC_MODEL` (default: `claude-3-5-haiku-20241022`)
- **State:** ✓ Present (configured)
- **Get Key:** https://console.anthropic.com/settings/keys
- **Endpoint:** `api.anthropic.com`
- **Streaming:** Yes
- **Use Case:** High-quality reasoning, long-context reasoning
- **Notes:** Free tier available. Recommended default.

#### 2. **OpenAI ChatGPT** ✅
- **API Key:** `OPENAI_API_KEY` (format: `sk-...`)
- **Model Var:** `OPENAI_MODEL` (default: `gpt-4o-mini`)
- **State:** ✓ Present (configured)
- **Get Key:** https://platform.openai.com/api-keys
- **Endpoint:** `api.openai.com`
- **Streaming:** Yes
- **Use Case:** Fast inference, cost-effective chat
- **Notes:** Pay-as-you-go. Widely compatible.

#### 3. **Google Gemini** ✅
- **API Key:** `GEMINI_API_KEY` (or `GOOGLE_API_KEY` as fallback)
- **Model Var:** `GEMINI_MODEL` (default: `gemini-2.5-flash`)
- **State:** ✓ Present (configured)
- **Get Key:** https://aistudio.google.com/app/apikey
- **Endpoint:** `generativelanguage.googleapis.com`
- **Streaming:** Yes
- **Use Case:** Vision/multimodal, fast responses
- **Notes:** Free tier generous (up to 1500 calls/min). Gemini 1.5 Flash available.

#### 4. **xAI Grok** ⏳ (Declared, Not Yet Implemented)
- **API Key:** `XAI_API_KEY`
- **Model Var:** `XAI_MODEL` (default: `grok-3-mini`)
- **State:** ✓ Present (configured) — but not yet in fallback chain
- **Get Key:** https://console.x.ai/
- **Endpoint:** `api.x.ai` (OpenAI-compatible)
- **Streaming:** Yes
- **Use Case:** Creative tasks, humor/personality
- **Notes:** OpenAI API-compatible. Real-time web access. **Reserved for future implementation** — currently declared in PCSF but not yet wired into fallback logic.

#### 5. **Ollama Local** ✅
- **Base URL:** `OLLAMA_BASE_URL` (default: `http://127.0.0.1:11434`)
- **Model Var:** `OLLAMA_MODEL` (default: `llama3`)
- **State:** ✓ Present (configured)
- **Installation:** https://ollama.ai
- **Endpoint:** Local HTTP server
- **Streaming:** Yes
- **Use Case:** Privacy-first, offline, no API keys
- **Notes:** Must run `ollama serve` separately. Install models via `ollama pull <model>`.

---

### OPTIONAL (Configured but Unused)

#### 6. **Mistral AI**
- **API Key:** `MISTRAL_API_KEY`
- **Model Var:** `MISTRAL_MODEL` (default: `mistral-large-latest`)
- **State:** ✗ Absent (not configured)
- **Get Key:** https://console.mistral.ai/api-keys/
- **Endpoint:** `api.mistral.ai`
- **Streaming:** Yes
- **Use Case:** Coding (Codestral), long-context chat
- **Cost:** Competitive pricing

#### 7. **Cohere**
- **API Key:** `COHERE_API_KEY`
- **Model Var:** `COHERE_MODEL` (default: `command-r-plus`)
- **State:** ✗ Absent (not configured)
- **Get Key:** https://dashboard.cohere.com/api-keys
- **Endpoint:** `api.cohere.com`
- **Streaming:** Yes
- **Use Case:** Long-context RAG, summarization
- **Cost:** Per-token, free tier for testing

#### 8. **Perplexity AI**
- **API Key:** `PERPLEXITY_API_KEY`
- **Model Var:** `PERPLEXITY_MODEL` (default: `sonar-pro`)
- **State:** ✗ Absent (not configured)
- **Get Key:** https://www.perplexity.ai/settings/api
- **Endpoint:** `api.perplexity.ai`
- **Streaming:** Yes
- **Use Case:** Search-augmented QA with live citations
- **Cost:** Per-token

#### 9. **DeepSeek**
- **API Key:** `DEEPSEEK_API_KEY`
- **Model Var:** `DEEPSEEK_MODEL` (default: `deepseek-chat`)
- **State:** ✗ Absent (not configured)
- **Get Key:** https://platform.deepseek.com/api_keys
- **Endpoint:** `api.deepseek.com`
- **Streaming:** Yes
- **Use Case:** Math/logic reasoning (DeepSeek-Reasoner)
- **Cost:** Low-cost reasoning-focused
- **Notes:** Emerging provider with strong reasoning capabilities.

#### 10. **OpenRouter**
- **API Key:** `OPENROUTER_API_KEY`
- **Model Var:** `OPENROUTER_MODEL` (default: `openai/gpt-4.1-mini`)
- **State:** ✗ Absent (not configured)
- **Get Key:** https://openrouter.ai/settings/keys
- **Endpoint:** `api.openrouter.ai`
- **Streaming:** Yes
- **Use Case:** Unified gateway to 100+ models, fallback routing, price optimization
- **Cost:** Per-token
- **Notes:** Can access models from all other providers through single API.

---

### VOICE/TTS (Not an LLM but Integrated)

#### 11. **ElevenLabs TTS** 🔊
- **API Key:** `ELEVENLABS_API_KEY`
- **Voice ID:** `ELEVENLABS_VOICE_ID` (default: `Rachel`)
- **State:** ✓ Present (configured)
- **Get Key:** https://elevenlabs.io/app/sign-up
- **Use Case:** High-quality voice output for responses
- **Notes:** Fallback chain: ElevenLabs → OpenAI TTS → Browser TTS

---

## Current Status

**As of 2026-06-08 21:15 UTC:**

### Live Fallback Chain (Actively Implemented)

| Provider | Implemented | API Key | Code Path | Order |
|----------|-------------|---------|-----------|-------|
| Gemini (Google) | ✅ Yes | Present | dream-chat.js:260 | #1 |
| Claude (Anthropic) | ✅ Yes | Present | dream-chat.js:300 | #2 |
| OpenAI | ✅ Yes | Present | dream-chat.js:344 | #3 |
| Ollama (Local) | ✅ Yes | Optional | dream-chat.js:387 | #4 |

### Declared in PCSF (Not Yet Implemented)

| Provider | Status | API Key | Reason |
|----------|--------|---------|--------|
| Grok (xAI) | ⏳ Declared | Configured | Reserved for future implementation |
| Mistral | ⏳ Declared | Absent | Not yet implemented |
| Cohere | ⏳ Declared | Absent | Not yet implemented |
| Perplexity | ⏳ Declared | Absent | Not yet implemented |
| DeepSeek | ⏳ Declared | Absent | Not yet implemented |
| OpenRouter | ⏳ Declared | Absent | Not yet implemented |

---

## Fallback Chain (Active Providers)

**Order used when a provider fails or key is absent (implemented in code):**

```
1. Gemini (Google)         ← Starts here (line 260)
2. Claude (Anthropic)      ← Next if Gemini fails (line 300)
3. OpenAI (ChatGPT)        ← Next if OpenAI fails (line 344)
4. Ollama (Local)          ← Last resort (line 387)
5. Local Persona Fallback  ← No network required (line 437)
```

⚠️ **Note:** xAI/Grok is declared in `provider.pcsf.json` but NOT YET implemented in the fallback chain code. It's reserved for future implementation.

**Where it's defined:**
- `data/pcsf/provider.pcsf.json` line 50–56: PCSF declarations (includes 5 active providers)
- `apps/lantern-garage/lib/dream-chat.js` lines 260–437: Actual fallback chain implementation
- Each provider checks: `const XXX_Key = process.env.XXX_API_KEY; if (XXX_Key && ...)`

---

## How to Use a Provider

### Set Up a New Provider

1. **Get the API key** from the provider's console (see table above)
2. **Add to `.env`:**
   ```bash
   echo "PROVIDER_API_KEY=your_key_here" >> .env
   echo "PROVIDER_MODEL=model_name" >> .env
   ```
3. **Hot-reload** (no restart needed):
   ```bash
   curl -X POST http://127.0.0.1:4177/api/settings/providers \
     -H "Content-Type: application/json" \
     -d '{"key": "PROVIDER_API_KEY", "value": "sk-..."}'
   ```
4. **Verify it works:**
   ```bash
   curl http://127.0.0.1:4177/api/settings/providers
   ```

### Change the Fallback Order

Edit `data/pcsf/provider.pcsf.json` line 50–56:
```json
"fallback_chain": [
  "gemini",
  "anthropic",
  "openai",
  "xai",
  "ollama"
]
```

Then restart the server or manually refresh the PCSF cache.

### Use a Specific Provider

In the Dream Chat UI (port 4177):
1. Click ⚙️ **Settings**
2. Select provider from dropdown
3. Add API key if needed
4. Save

Or via API:
```bash
curl -X POST http://127.0.0.1:4177/api/dream/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "hello", "provider": "claude"}'
```

---

## Environment File Locations

| File | Purpose | Status |
|------|---------|--------|
| `.env.example` | Template (version controlled) | ✅ In repo |
| `.env` | Live config (git-ignored) | 🔒 Local only |
| `.env.local` | User secrets (git-ignored) | 🔒 Optional |

**Load order (first match wins):**
1. `.env.local` (user overrides)
2. `.env` (local config)
3. `.env.example` (fallback defaults)

---

## Server Configuration

| Component | File | Port | Purpose |
|-----------|------|------|---------|
| **Lantern Garage** | `apps/lantern-garage/server.js` | 4177 | Main web server + API |
| **MCP Server** | `src/mcp_server/server.py` | 8771 | Tool integration (optional) |
| **Ollama** | `ollama serve` | 11434 | Local LLM (optional) |

---

## Security Notes

⚠️ **API Keys:**
- Never commit `.env` to git (already in `.gitignore`)
- Rotate keys if accidentally exposed
- Use separate keys for dev/prod
- Consider OpenRouter for provider isolation (single key for all)

⚠️ **Local Ollama:**
- No authentication by default on `127.0.0.1:11434`
- For production, use reverse proxy + auth
- Models stored in `~/.ollama/` (check disk space)

---

## Status As of This Session

✅ **Currently Running:**
- Ollama: Started with `ollama serve` (responsive)
- Lantern Garage: Dual-boot (port 4177 stable, 4178 dev)
- Dream Chat UI: Fully functional

✅ **Verified Working:**
- Three Doors game: `!three-doors` command responded
- Fallback chain: Ollama caught request when no cloud keys set
- Multi-provider architecture: All 5 configured providers registered

**Last Updated:** 2026-06-08 10:42 UTC  
**Documentation Version:** 1.0.0  
**PCSF Provider Version:** provider.pcsf.json (1.0.0)
