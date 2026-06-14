# Lantern OS — Quick Start

Get every service running in under 5 minutes.

---

## Dual Boot Quickstart (Recommended)

**Start both stable release and dev server simultaneously:**

```powershell
make quickstart
```

Or directly:
```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File start-dual-servers.ps1
```

**What this does:**
- **Port 4177**: Stable tagged release (checks out master, pulls latest)
- **Port 4178**: Development version (your current working branch)
- Opens Chrome to http://127.0.0.1:4177/dream-chat.html
- **Public access** (via Cloudflare Tunnel): https://lantern-os.net

**Dual boot means:** You can test stable releases while developing on the same machine without conflicts.

---

## Prerequisites

**First, read the provider documentation:** See [**PROVIDERS.md**](PROVIDERS.md) for inventory of all 10 AI providers, configuration, and current status.

```bash
node --version   # v18+ recommended
python --version # v3.10+ recommended
```

**Local must be on master, synced with remote:**

```bash
git checkout master
git pull origin master
```

All local dev and autostart boots run from the `master` branch. Feature branches are for PRs only — never run the server from a feature branch. Always merge upstream before starting.

**Versioning:** Version auto-bumps on each commit (patch), with timestamp on build. Check `apps/lantern-garage/version.json` for build ID and timestamp.

Install dependencies:

```bash
npm install --prefix apps/lantern-garage
python -m pip install -r requirements.txt
```

**New user setup (one-time):**

1. Copy `.env.example` → `.env` and fill in your keys:
   ```
   DISCORD_BOT_TOKEN=your_bot_token
   LANTERN_DISCORD_GUILD_ID=your_server_id
   ANTHROPIC_API_KEY=sk-ant-...   # or GEMINI_API_KEY / OPENAI_API_KEY
   ```
2. Install ffmpeg for voice/music (optional, enables `!lounge` / `!dreams` / `!focus`):
   ```powershell
   winget install Gyan.FFmpeg
   ```
3. Start everything: `npm run dev --prefix apps/lantern-garage`
   — the server auto-starts the Discord bot when token keys are set.

---

## 1. Autostart (One-Time Setup — Machine Manages It After This)

Register Lantern OS as a Windows startup task. Once set up, **the computer handles start, crash recovery, and restart automatically** — no one needs to touch it:

```powershell
# Run once (as Admin) — never need to run again
.\scripts\Start-Lantern.ps1 -RegisterAutostart
```

What this registers:
- Triggers: **at system boot** and **at every login**
- Boot sequence: `git pull origin master` → HFF seed → `node --watch server.js`
- Crash recovery: restarts automatically, unlimited times, 1-minute backoff
- Logs to: `logs\lantern-autostart.log`

To remove the autostart task:
```powershell
.\scripts\Start-Lantern.ps1 -UnregisterAutostart
```

---

## 2. Manual Boot (Dev / One-Off)

If you want to start the server manually without the autostart task:

```powershell
# Full boot: git pull → HFF seed → node --watch
npm run start:master --prefix apps/lantern-garage
```

What it does in order:
1. `git pull origin master` — always on master, never a feature branch
2. `python3 integrations/human-flourishing-frameworks/export_snapshot.py` — seeds HFF world-model and writes `data/snapshot.json`
3. `node --watch server.js` — starts server, auto-restarts on any file change

**Dev mode (no git pull, no HFF seed):**

```bash
npm run dev --prefix apps/lantern-garage
```

Open locally: `http://127.0.0.1:4177` — the Dream Journal chat UI.

Or access publicly: `https://lantern-os.net` (via Cloudflare Tunnel)

**Discord bot starts automatically** when `DISCORD_BOT_TOKEN` and `LANTERN_DISCORD_GUILD_ID`
are set in `.env`. No separate terminal needed — the server spawns it as a child process.

The bot includes the Sinatra Lounge voice player and binaural beats.
Voice requires ffmpeg: `winget install Gyan.FFmpeg` (one-time, Windows).

**Optional services (separate terminals):**

```bash
# MCP server (port 8771)
python src/mcp_server/server.py

# Convergence loop (one-shot)
python src/convergence_io_engine.py loop
```

**What you get:**
- Dream Journal chat UI (`/`)
- API routes (`/api/dream/*`, `/api/settings/providers`)
- Static assets and PWA manifest
- SSE streaming chat endpoint

---

## 3. Configure AI Providers (Optional but Recommended)

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

## 4. Start the MCP Server (Optional)

```bash
python src/mcp_server/server.py
```

**Local access:** `http://127.0.0.1:8771`

**Public access (via Cloudflare Tunnel):** `https://mcp.lantern-os.net`

**What you get:**
- Tool discovery endpoint
- Agent slot registration
- Local-first runtime verification

### 4a. OAuth2-Protected MCP Server (Optional)

For external integrations with OAuth2 authentication:

```bash
python src/mcp_server/server_oauth.py
```

**Local access:** `http://127.0.0.1:8772`

**Public access (via Cloudflare Tunnel):** `https://mcp.lantern-os.net/oauth`

Supports OAuth2 providers:
- **Google** — `https://mcp.lantern-os.net/oauth/authorize?provider=google`
- **GitHub** — `https://mcp.lantern-os.net/oauth/authorize?provider=github`
- **Discord** — `https://mcp.lantern-os.net/oauth/authorize?provider=discord`

---

## 5. Start the Convergence Orchestrator (Optional)

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

## 6. Start the Discord Bot (Optional)

Requires `DISCORD_BOT_TOKEN` and `LANTERN_DISCORD_GUILD_ID` in `.env.local`.

```bash
python src/discord_lounge_bot/bot.py
```

---

## 7. Enable Voice Features (Optional)

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

## 8. Run Tests

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

## 9. Archive Cleanup → Google Drive (Maintenance)

Old artifacts, large PDFs, and historical snapshots should move to Google Drive to keep the repo lean.

```powershell
# Review what would be archived (dry run)
powershell -File .\scripts\Invoke-ArchiveCommonsBatch.ps1 -DryRun

# Execute archive batch
powershell -File .\scripts\Invoke-ArchiveCommonsBatch.ps1
```

After running, move `archive/reports-YYYY-MM-DD/` and `archive/manifests-*-YYYY-MM-DD/` folders to your Google Drive `Lantern-OS-Archive/` folder, then delete the local copies.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| Server not starting after reboot | Check `logs\lantern-autostart.log`; run `-RegisterAutostart` again if task is missing |
| `ECONNREFUSED` on port 4177 | Check if another process is using the port: `lsof -i :4177` |
| No AI responses | Verify at least one provider key is set in `.env.local` |
| TTS not speaking | Check browser console; if ElevenLabs key is set, verify quota |
| MCP server not found | Ensure `src/mcp_server/server.py` is running on port 8771 |
| Tests fail | Make sure the web server is running before running API tests |

---

## 10. Public Deployment via Cloudflare Tunnel (Automatic)

The Cloudflare tunnel now starts automatically with `npm start` — no separate command needed!

**One-time setup:**

```bash
# Install Cloudflare tunnel agent
choco install cloudflare-warp

# Authenticate (one-time, opens browser)
cloudflared tunnel login

# Create tunnel (one-time)
cloudflared tunnel create lantern-os
```

Then access publicly:
- **Dream Journal:** `https://lantern-os.net`
- **MCP (public):** `https://mcp.lantern-os.net`
- **MCP (OAuth2):** `https://mcp.lantern-os.net/oauth`

The tunnel will start automatically whenever you run `npm start` (can disable with `LANTERN_CLOUDFLARE_TUNNEL=false`).

**Manual tunnel start (if not using npm start):**

```bash
# Run tunnel (connects local ports to public domain)
cloudflared tunnel run lantern-os --config cloudflare-config.yml
```

Then access:
- **Dream Journal:** `https://lantern-os.net`
- **MCP Server:** `https://mcp.lantern-os.net`

See [`docs/CLOUDFLARE-TUNNEL-DEPLOYMENT.md`](docs/CLOUDFLARE-TUNNEL-DEPLOYMENT.md) for full setup guide.

---

## Next Steps

- Read [`AGENTS.md`](AGENTS.md) for agent workflow rules
- Read [`docs/CONVERGENCE-LOOP.md`](docs/CONVERGENCE-LOOP.md) for the 12-phase method
- Check [`manifests/dream-journal-v1-agent-slots.json`](manifests/dream-journal-v1-agent-slots.json) for active work items
- Deploy publicly: [`docs/CLOUDFLARE-TUNNEL-DEPLOYMENT.md`](docs/CLOUDFLARE-TUNNEL-DEPLOYMENT.md)
