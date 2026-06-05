# Lantern OS

[![CI](https://github.com/alex-place/lantern-os/actions/workflows/ci.yml/badge.svg)](https://github.com/alex-place/lantern-os/actions/workflows/ci.yml)
[![Deploy](https://github.com/alex-place/lantern-os/actions/workflows/deploy.yml/badge.svg)](https://github.com/alex-place/lantern-os/actions/workflows/deploy.yml)
[![Validate Dream Journal](https://github.com/alex-place/lantern-os/actions/workflows/validate-dream-journal.yml/badge.svg)](https://github.com/alex-place/lantern-os/actions/workflows/validate-dream-journal.yml)

**Local-first OS cockpit for symbolic memory, agentic convergence, and dream journaling.**

Built by Alex Place. All data stays on your machine. No accounts required.

**Current Focus (2026-06):** Dream Journal V1.0.0 Orion Edition + single-container web/Discord convergence.

---

## Purpose & Philosophy

Lantern OS is designed around three principles:

1. **Local-first** — Your journal, memories, and agent conversations never leave your device unless you explicitly export them.
2. **Privacy-first** — No telemetry, no cloud storage, no accounts. API keys are stored in `.env.local` (gitignored).
3. **Agentic convergence** — Multiple AI agents (personas) route through a unified provider chain, converging on a single coherent response. The system learns from interaction patterns and stores them in a symbolic memory engine (CSF/CADD).

### What it does today

| Component | Description |
|-----------|-------------|
| **Dream Journal** | Freeform RP chat interface. No hardcoded fields — just talk. Data stored in browser `localStorage` with JSONL export. Multi-provider AI streaming with persona routing. |
| **Lantern Garage** | Node.js HTTP server (`apps/lantern-garage/server.js`) serving the Dream Journal UI and REST API on port 4177. |
| **Convergence IO Engine** | 12-phase orchestrator (`src/convergence_io_engine.py`) that inspects repo state, identifies sources, validates health, and recommends next work items. |
| **CSF / CADD Memory Engine** | Context Archive for Dream Data (`src/csf/memory_engine.py`). JSONL-based memory tiers (Trace -> Anchor -> Entity -> Skill -> Export) with keyword/entity inverted indexes. |
| **Multi-Provider Gateway** | Unified connector (`src/unified_agent_connector.py`) routing to Gemini, Claude, OpenAI, Grok, and Ollama with health checks and fallback chains. |
| **Discord Bot** | Slash-command Discord bot (`src/discord_lounge_bot/bot.py`) with role-gated tiered access, sharing the same convergence pipeline as the web UI. |
| **MCP Server** | Model Context Protocol server (`src/mcp_server/server.py`) exposing repo health, task intake, fleet status, and skill dispatch to IDE agents (Windsurf/Cascade). |
| **PWA** | Installable offline app (`apps/lantern-garage/public/sw.js`) with IndexedDB queue and background sync for offline dream creation. |

### What is NOT in scope

- No live trading or financial execution.
- No production Stripe integration (payment bridge is a stub).
- No actual outreach automation (outreach scripts are drafts only).
- No cloud data storage — all journal data stays on your machine.

---

## Architecture

```
lantern-os/
├── apps/
│   └── lantern-garage/          # Node.js web server + Dream Journal UI
│       ├── server.js             # Entry point (90 lines, loads routes)
│       ├── routes/               # 7 domain route modules
│       ├── lib/                  # streaming, chat, store modules
│       └── public/               # HTML surfaces, PWA manifest, service worker
├── src/
│   ├── convergence_io_engine.py  # 12-phase orchestrator (health, inspect, loop, converge)
│   ├── unified_agent_connector.py# Multi-provider AI gateway with health checks
│   ├── csf/
│   │   └── memory_engine.py      # Symbolic memory engine (JSONL tiers + indexes)
│   ├── mcp_server/
│   │   └── server.py             # MCP tools for IDE integration
│   ├── discord_lounge_bot/
│   │   └── bot.py                # Discord slash-command bot
│   └── hff-api/                  # Research API (bias monitoring, public datasets)
├── data/
│   └── pcsf/                     # Provider Convergence State Files (health, models, agents)
├── manifests/                    # System manifests, architecture docs, work queues
├── csf/ingest/                   # CSF ingestion docs = task queue (pick one and implement)
├── tests/                        # Node.js + Python test suites
├── docs/                         # User guides, quickstarts, connector docs
└── scripts/                      # Utility scripts, validation, orchestration
```

---

## The Convergence System

Lantern OS uses a **Tesseract Engine** with 4 layers that route work from fast/fault-tolerant (inner) to slow/deliberate (outer):

| Layer | Name | Role |
|-------|------|------|
| 1 | **Surface** | Persona matching, keyword routing, quick replies |
| 2 | **Interface** | Provider selection, health checks, rate-limit handling |
| 3 | **Convergence** | MemOS semantic retrieval, RAG fallback, context assembly |
| 4 | **Core** | Model inference, streaming, response generation |

The **Convergence IO Engine** (`src/convergence_io_engine.py`) runs a 12-phase loop:

```bash
# Check system health
python src/convergence_io_engine.py health

# Run the full convergence loop
python src/convergence_io_engine.py loop

# Ask the orchestrator what to work on next
python src/convergence_io_engine.py converge --message "what should I work on next" --persona keystone

# Inspect slots, metrics, and circuits
python src/convergence_io_engine.py inspect
```

Read the full architecture in `manifests/TESSERACT-ARCHITECTURE.md`.

---

## Agent System

Lantern OS uses **6 symbolic personas** that route based on keyword matching in user messages:

| Persona | Symbol | Vibe |
|---------|--------|------|
| **Keystone** | truth, pattern, anchor | Grounded integrator |
| **Waterfall** | water flowing, reconnection | Gentle, healing, patient |
| **Xenon** | spacecraft, navigation | Exploratory, collaborative |
| **Blinkbug** | static, glitch, chaos | Chaotic, creative, unhinged |
| **Comet Leap** | trajectory, momentum | Fast, energetic, flourishing |
| **Founder** | wish, protection, lantern | Protective, honest, grounded |

All personas share the same multi-provider backend but receive different system prompts. The **Keystone** persona can bypass the normal flow for raw dev/debug access.

The agent system is described in detail in `src/unified_agent_connector.py` and `data/pcsf/agent.pcsf.json`.

---

## How to run

### Prerequisites

```bash
node --version   # v20 or higher
python --version # 3.11 or higher (optional, for MCP + Convergence IO)
```

### Local (default)

```bash
# Start the main web server
node apps/lantern-garage/server.js
# opens at http://127.0.0.1:4177
```

Or with npm:

```bash
npm start --prefix apps/lantern-garage
```

### All services

```bash
# Terminal 1 — Garage (web UI + API)
node apps/lantern-garage/server.js

# Terminal 2 — MCP Server (optional, for IDE integration)
python src/mcp_server/server.py

# Terminal 3 — Discord Bot (requires DISCORD_BOT_TOKEN)
python src/discord_lounge_bot/bot.py
```

### Cloud (Railway)

Railway auto-deploys from `master`. Set `PORT` in Railway environment variables; the server binds to `0.0.0.0` when `PORT` is present.

### Static UI (GitHub Pages)

Static surfaces deploy from the `gh-pages` branch via GitHub Actions in `.github/workflows/`.

---

## Testing

```bash
# Node.js API tests (requires running server)
node tests/test_dream_journal_api.js       # 18 tests
node tests/test_dream_chat_multiturns.js     # 11 tests

# Python tests
python -m pytest tests/ -q --tb=short --ignore=tests/test_anti_entropy_memory.py --ignore=tests/test_audit_chain.py --ignore=tests/test_discord_bot.py --ignore=tests/test_discord_voice_gate.py

# Validate from garage directory
npm run validate --prefix apps/lantern-garage
```

---

## Documentation

| Document | Purpose |
|----------|---------|
| **[AGENTS.md](AGENTS.md)** | Critical reading for AI coding agents. Token-saving contract, real-vs-design rules, monoworkstream workflow, key file locations. **Read this first before editing.** |
| **[CONTRIBUTING.md](CONTRIBUTING.md)** | Dev setup, branch conventions, repo contract, code style, secrets policy. |
| **[CHANGELOG.MD](CHANGELOG.MD)** | Release notes, known bugs, verification status. |
| **[docs/DREAM-JOURNAL-USER-GUIDE.md](docs/DREAM-JOURNAL-USER-GUIDE.md)** | Full user guide for the Dream Journal chat interface. |
| **[docs/DREAM-JOURNAL-QUICKSTART.md](docs/DREAM-JOURNAL-QUICKSTART.md)** | Quick-start guide for new users. |
| **manifests/TESSERACT-ARCHITECTURE.md** | 4-layer hypercube architecture deep-dive. |
| **csf/ingest/*.md** | CSF ingestion docs = the task queue. Each file has problem + implementation sketch + files to change. |

---

## IDE Integration (Windsurf / Cascade MCP)

The Lantern OS MCP server links to Windsurf/Cascade via a stdio bridge.

1. Start the MCP server:
   ```bash
   python src/mcp_server/server.py
   ```
2. Windsurf reads `.windsurf/mcp.json` and connects through `scripts/mcp_stdio_bridge.py`.
3. Exposed tools: `queue_status`, `task_intake`, `dispatch_work`, `boot_check`, `list_skills`, `get_status`, `fleet_status`.

---

## Deployed URLs

| Environment | URL | Description |
|-------------|-----|-------------|
| **GitHub Pages** | https://alex-place.github.io/lantern-os/ | Static UI (pitch, proof, pricing, wish-door, dream-journal) |
| **Repository** | https://github.com/alex-place/lantern-os | Source code, issues, PRs |

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for full details.

Quick reference:
- Branch off `master`: `<type>/<short-description>` (e.g., `feat/convergence-io-tier`, `fix/mcp-dotenv`)
- One open PR at a time (monoworkstream rule)
- Both Node.js and Python test suites must pass before merging
- Never commit secrets — `.env` and `data/dream_journal/` are gitignored

---

## License & Privacy

All dream journal data is stored locally in your browser and in `data/dream_journal/` (gitignored). See [PRIVACY_AND_OFFLINE.md](PRIVACY_AND_OFFLINE.md) for the family-marketing privacy stance.

---

*Last updated: 2026-06-05 — Dream Journal Orion Edition v1.0.0*
