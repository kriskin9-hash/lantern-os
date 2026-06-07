# Lantern OS — Quick Start

Get every service running in under 5 minutes.

---

## Prerequisites

```bash
node --version   # v18+ recommended
python --version # v3.10+ recommended
```

Install dependencies:

```bash
npm install --prefix apps/lantern-garage
python -m pip install -r requirements.txt
```

---

## 1. Start the Core Web Server (Required)

**Development (recommended — auto-restarts on file changes):**

```bash
npm run dev --prefix apps/lantern-garage
```

**Production / one-shot:**

```bash
npm start --prefix apps/lantern-garage
# or directly:
node apps/lantern-garage/server.js
```

Open `http://127.0.0.1:4177` — the Dream Journal chat UI.

**What you get:**
- Dream Journal chat UI (`/`)
- API routes (`/api/dream/*`, `/api/settings/providers`)
- Static assets and PWA manifest
- SSE streaming chat endpoint

---

## 2. Configure AI Providers (Optional but Recommended)

Open the settings drawer (gear icon) in the chat UI and add at least one key:

| Provider | Key | Why |
|---|---|---|
| Gemini | `GEMINI_API_KEY` | Fastest free tier, generous quota |
| Claude | `ANTHROPIC_API_KEY` | High-quality reasoning |
| OpenAI | `OPENAI_API_KEY` | GPT-4o-mini for cost-efficient chat |
| Grok | `XAI_API_KEY` | Alternative frontier model |

Or set via `.env.local`:

```bash
echo "GEMINI_API_KEY=your_key_here" > apps/lantern-garage/.env.local
```

The server hot-reloads keys on save — no restart needed.

---

## 3. Start the MCP Server (Optional)

```bash
python src/mcp_server/server.py
```

**Port:** `8771`

**What you get:**
- Tool discovery endpoint
- Agent slot registration
- Local-first runtime verification

---

## 4. Start the Convergence Orchestrator (Optional)

```bash
# Health check
python src/convergence_io_engine.py health

# Full 12-phase convergence loop
python src/convergence_io_engine.py loop

# Ask the AI what to work on next
python src/convergence_io_engine.py converge --message "what should I work on next" --persona keystone

# Inspect slots, metrics, circuits
python src/convergence_io_engine.py inspect
```

---

## 5. Start the Discord Bot (Optional)

Requires `DISCORD_BOT_TOKEN` and `LANTERN_DISCORD_GUILD_ID` in `.env.local`.

```bash
python src/discord_lounge_bot/bot.py
```

---

## 6. Enable Voice Features (Optional)

### Browser TTS/STT (No setup)
- Chrome/Edge: Web Speech API works out of the box
- Click the microphone button for STT
- Responses auto-speak via browser TTS

### ElevenLabs TTS (Higher quality)
Add to `.env.local`:

```bash
ELEVENLABS_API_KEY=sk_...
ELEVENLABS_VOICE_ID=Rachel
```

The chat UI will detect the key and route TTS through ElevenLabs first, OpenAI TTS second, browser TTS last.

---

## 7. Run Tests

```bash
# API tests (requires running server)
node tests/test_dream_journal_api.js
node tests/test_dream_chat_multiturns.js

# Python tests
python -m pytest tests/ -q --tb=short

# Playwright E2E tests
npm run test:e2e --prefix apps/lantern-garage
```

---

## 8. Archive Cleanup → Google Drive (Maintenance)

Old artifacts, large PDFs, and historical snapshots should move to Google Drive to keep the repo lean.

```powershell
# Review what would be archived (dry run)
powershell -File .\scripts\Invoke-ArchiveCommonsBatch.ps1 -DryRun

# Execute archive batch
powershell -File .\scripts\Invoke-ArchiveCommonsBatch.ps1
```

After running, move `archive/reports-YYYY-MM-DD/` and `archive/manifests-*-YYYY-MM-DD/` folders to your Google Drive `Lantern-OS-Archive/` folder, then delete the local copies.

---

## Full Stack Startup (One of Everything)

Terminal 1 — Web server:
```bash
node apps/lantern-garage/server.js
```

Terminal 2 — MCP server:
```bash
python src/mcp_server/server.py
```

Terminal 3 — Convergence loop (one-shot):
```bash
python src/convergence_io_engine.py loop
```

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `ECONNREFUSED` on port 4177 | Check if another process is using the port: `lsof -i :4177` |
| No AI responses | Verify at least one provider key is set in `.env.local` |
| TTS not speaking | Check browser console; if ElevenLabs key is set, verify quota |
| MCP server not found | Ensure `src/mcp_server/server.py` is running on port 8771 |
| Tests fail | Make sure the web server is running before running API tests |

---

## Next Steps

- Read [`AGENTS.md`](AGENTS.md) for agent workflow rules
- Read [`docs/CONVERGENCE-LOOP.md`](docs/CONVERGENCE-LOOP.md) for the 12-phase method
- Check [`manifests/dream-journal-v1-agent-slots.json`](manifests/dream-journal-v1-agent-slots.json) for active work items
