# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Lantern OS is a local-first OS cockpit built by a solo developer (Alex Place). The primary deliverable is a **Dream Journal** — a freeform RP chat interface backed by a Node.js server, with a Python MCP server and optional Discord bot.

## Commands

### Python tests

```bash
# Install dependencies
python -m pip install -r requirements.txt

# Run all tests (safe subset — excludes known-broken/integration tests)
python -m pytest tests/ -q --tb=short \
  --ignore=tests/test_anti_entropy_memory.py \
  --ignore=tests/test_audit_chain.py \
  --ignore=tests/test_discord_bot.py \
  --ignore=tests/test_discord_voice_gate.py

# Run a single test file
python -m pytest tests/test_dream_journal.py -q --tb=short

# Run a specific test function
python -m pytest tests/test_dream_journal.py::test_function_name -q
```

### Node.js (lantern-garage)

```bash
# Start main web server (port 4177)
node apps/lantern-garage/server.js
# or
npm start --prefix apps/lantern-garage

# Syntax-check JS files
make check-node        # runs node --check on server.js + cloud-server.js

# Node API/chat tests (server must be running)
npm run test:api --prefix apps/lantern-garage
npm run test:chat --prefix apps/lantern-garage
npm run test:ui --prefix apps/lantern-garage   # requires Playwright
```

### Python services

```bash
# MCP server (port 8771)
python src/mcp_server/server.py

# GPT Web API (port 3000) — separate Node service
node services/gpt-web-api/server.js

# Discord bot
python src/discord_lounge_bot/bot.py
```

### Docker (Dream Journal stack)

```bash
make build-dream
make up-dream
make down-dream
make logs-dream
```

## Architecture

### Core data flow

The **Lantern Garage server** (`apps/lantern-garage/server.js`) is the single entrypoint. It:
- Serves all static HTML/JS from `apps/lantern-garage/public/`
- Routes REST API calls (`/api/*`) using plain `if` blocks (no framework)
- Streams LLM replies via SSE at `/api/dream/stream`
- Reads/writes persistent state as `.json` and `.jsonl` files under `data/`

Business logic is split into `apps/lantern-garage/lib/`:
| Module | Responsibility |
|--------|----------------|
| `dream-chat.js` | Agent persona selection + LLM call routing (Anthropic/OpenAI/Gemini) |
| `stream-chat.js` | SSE streaming handler |
| `dreamer-store.js` | Per-user dream notebook JSONL persistence |
| `conversation-store.js` | Conversation log append/read |
| `rag-house.js` | Flat RAG document house builder |
| `status.js` | System/readiness/mining-lab status aggregation |
| `file-queue.js` | Async JSONL append queue (avoids concurrent write corruption) |

### Dream Journal agents

Six agent personas are defined in `apps/lantern-garage/lib/dream-chat.js`: `lantern`, `blinkbug`, `keystone`, `waterfall`, `xenon`, `founder`. Each has a `systemPrompt`. `selectAgent()` scores inbound messages by keyword match; the winner's prompt is injected into the LLM call.

**Only these four skills have real implementations:** `dream_journal`, `lucid_dreaming`, `archive_curator`, `voice_curator`. All other `skills/*/SKILL.md` entries are design contracts only — do not claim they are live.

### MCP server

`src/mcp_server/server.py` is a FastAPI + SSE service exposing MCP tools (`queue_status`, `task_intake`, `dispatch_work`, `boot_check`, `list_skills`, `get_status`). Only register tools here that have real implementations.

### CSF (Convergence-Fitted Searchable Format)

`src/csf/` and `csf/` contain a custom binary archive format used for memory exports and symbolic data compression. See `caad/README.md` for the CADD (Context Archive for Dream Data) spec built on top of CSF.

### Cloud vs local

- **Local:** server binds to `127.0.0.1:4177`
- **Cloud (Railway):** `apps/lantern-garage/cloud-server.js` is the entrypoint; binds to `0.0.0.0` when `PORT` env var is set. Railway auto-deploys from `master`.
- **Static UI:** deployed from `gh-pages` branch via GitHub Actions; source in `apps/lantern-garage/public/`.

### Configuration

Copy `.env.example` to `.env` at repo root. Key variables: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `DISCORD_TOKEN`. The server loads `.env` from repo root at startup.

`pytest.ini` sets `pythonpath = apps src` so tests can import from both trees without install.

## Monoworkstream Rule (Critical)

This repo enforces **one open PR at a time**:
- No new commits or branches while a PR is open
- Install hooks: `powershell -ExecutionPolicy Bypass -File scripts/Install-MonoworkstreamHooks.ps1`
- Emergency bypass: `SKIP_MONOWORKSTREAM=1 git commit ...`

Always check for open PRs before creating branches or commits.
