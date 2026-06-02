# Lantern OS — Dream Journal

**Product:** Dream Journal by Lantern OS  
**Status:** Production (local)  
**Last Updated:** 2026-06-02  
**Created by:** Alex Place

> *Every dream is a door. Every memory is a home.*

---

## What This Is

Dream Journal is a **local-first, private journaling app** built on Lantern OS. Your dreams, reflections, and notes are saved on your own device. No cloud, no tracking, no ads.

- **Local** — runs at `http://127.0.0.1:4177`, never leaves your machine
- **Private** — all data in `data/dream_journal/*.jsonl`, plain text you own
- **Fast** — Node.js server, loads in under 1 second
- **Simple** — one form, four fields, one button

---

## Quick Start (Windows)

### Prerequisites

```powershell
node --version   # v20+ required
npm --version    # bundled with Node
git --version    # to clone/pull
```

Install Node.js from [nodejs.org](https://nodejs.org) if needed.

### Start the app

```powershell
cd C:\Users\alexp\OneDrive\Documents\GitHub\lantern-os
npm install --prefix apps/lantern-garage
npm start --prefix apps/lantern-garage
```

Open Chrome: **http://127.0.0.1:4177**

### Autostart (Windows — run once as Admin)

To have Lantern start automatically on login, create a Task Scheduler entry:

```powershell
# Run as Administrator — registers autostart task
$action = New-ScheduledTaskAction -Execute "node" `
  -Argument "apps\lantern-garage\server.js" `
  -WorkingDirectory "C:\Users\alexp\OneDrive\Documents\GitHub\lantern-os"

$trigger = New-ScheduledTaskTrigger -AtLogon

Register-ScheduledTask `
  -TaskName "LanternDreamJournal" `
  -Action $action `
  -Trigger $trigger `
  -RunLevel Highest `
  -Force

Write-Host "Lantern will now start automatically at login."
```

To remove autostart:
```powershell
Unregister-ScheduledTask -TaskName "LanternDreamJournal" -Confirm:$false
```

---

## Services

| Service | Port | Start Command | Notes |
|---------|------|--------------|-------|
| **Lantern Garage** (Dream Journal UI + API) | 4177 | `npm start --prefix apps/lantern-garage` | Primary service — start this first |
| **MCP Server** | 8771 | `.venv\Scripts\python.exe src\mcp_server\server.py` | Agent orchestration, optional |
| **Local Lantern Chat** | 8766 | Auto-started by MCP | Advisory chat, optional |
| **Discord Bot** | — | `.\lantern-discord\deploy-discord-bot.ps1` | Requires `DISCORD_BOT_TOKEN` env var |

**Minimum to run:** Only Lantern Garage (4177) is required for Dream Journal.

---

## Dream Journal Features

### Entry Types
| Type | Use |
|------|-----|
| `dream` | Nightly dreams, lucid experiences |
| `note` | Daytime thoughts, observations |
| `symbol` | Recurring images, archetypes |
| `reflection` | Analysis of patterns, meanings |

### Fields
- **Text** — free-form, required
- **Emotions** — comma-separated (clarity, wonder, awe, etc.)
- **Tags** — comma-separated, max 10 (project, season, recurring, etc.)
- **Lucidity** — 0.0 (fully asleep) to 1.0 (fully lucid)

### API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/dream/create` | Save a new entry |
| `GET` | `/api/dream/stats` | Aggregated stats (counts, top emotions, avg lucidity) |
| `GET` | `/api/dream/search?text=X&tags=Y` | Search by text or tags |
| `GET` | `/api/dream/read/:id` | Fetch one entry by ID |

### Data Storage
- `data/dream_journal/dreams_YYYY-MM.jsonl` — monthly append-only files
- Each entry: `id`, `timestamp`, `kind`, `text`, `lucidity`, `emotions`, `tags`, `symbols`
- Plain JSON lines — readable, portable, zero lock-in

---

## Architecture

```
Browser (Chrome)
    ↓ http://127.0.0.1:4177
apps/lantern-garage/server.js   ← Node.js HTTP server (no framework)
    ├── public/index.html        ← Dream Journal UI (white/purple theme)
    ├── /api/dream/*             ← REST endpoints
    └── data/dream_journal/      ← JSONL storage

skills/dream_journal/            ← Python skill (cognitive layer)
    ├── dream_journal.py         ← DreamJournal class (structured logging)
    └── cognitive_layer.py       ← BayesianFallacyDetector, DreamCharacter, CognitiveJournal

lore/LANTERN-CHARACTERS-AND-REALMS.md  ← Characters + symbolic realms
rag/seeds/                             ← RAG CAAD memory seeds
```

**Design constraints:**
- No external runtime dependencies for the UI (vanilla JS, no React/Vue)
- Local-only by default (`127.0.0.1`, not `0.0.0.0`)
- Write-queued appends (no concurrent JSONL corruption)
- All data readable without the app (plain text)

---

## Testing

### Python (Dream Journal skill)
```bash
python -m pytest tests/test_dream_journal.py -v
# 34/34 passing
```

### Node.js (REST API)
```bash
# Server must be running first
npm start --prefix apps/lantern-garage &
sleep 2
node tests/test_dream_journal_api.js
# 14/14 passing
```

### Run all tests
```bash
python -m pytest tests/ -v --ignore=tests/node_modules
node tests/test_dream_journal_api.js
```

---

## Repository Structure

```
lantern-os/
├── apps/
│   └── lantern-garage/          ← Dream Journal server + UI
│       ├── server.js            ← HTTP server, REST API
│       └── public/
│           └── index.html       ← Dream Journal UI
├── skills/
│   └── dream_journal/           ← Python cognitive layer
│       ├── dream_journal.py
│       └── cognitive_layer.py
├── lore/
│   └── LANTERN-CHARACTERS-AND-REALMS.md  ← Symbolic characters and realms
├── rag/seeds/                   ← RAG CAAD memory (9 seeds)
├── data/
│   ├── dream_journal/           ← JSONL dream entries (yours, private)
│   └── wallet/                  ← Invoice ledger (cleared cash = $0)
├── docs/
│   └── DREAM-JOURNAL-USER-GUIDE.md  ← End-user guide
└── tests/
    ├── test_dream_journal.py    ← 34 Python tests
    └── test_dream_journal_api.js ← 14 REST API tests
```

---

## Lore & Characters

The Dream Journal is grounded in Lantern OS lore. Characters and realms live in `lore/LANTERN-CHARACTERS-AND-REALMS.md`:

| Character | Role | Symbol |
|-----------|------|--------|
| **Captain Lantern Blinkbug** | Mascot, warm guide | Yellow glow, warmth |
| **Gage** | Artist-learner | Creative precision |
| **Mary Place** | Alex's mother | Waterfall, peacock |
| **Angela** | Courtney's mother | Healer, connector |
| **Courtney** | Navigator | Xenon spaceship |
| **Alex Place** | Founder/operator | Keys, vision |

---

## Wallet Truth

```
Cleared cash: $0     ← real until payment receipt logged
Pending invoices: $398
Operating rule: Do not claim revenue until funds clear.
```

---

## Operator Principles

1. **Memory is not proof** — RAG seeds are evidence artifacts, operator corrections override them
2. **Default-closed writes** — no repo mutation without explicit approval
3. **Local-first** — the machine is the source of truth
4. **Visible flame** — system state is always inspectable

---

**Last Updated:** 2026-06-02  
**Next milestone:** Discord bot integration + per-user journal customization
