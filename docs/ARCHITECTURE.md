# Lantern OS — Architecture

Current-state architecture as of 2026-06-02.

---

## Components

### `apps/lantern-garage/`

Node.js HTTP server that is the runtime core of Lantern OS.

| File | Role |
|---|---|
| `server.js` | Local development server. Listens on `LANTERN_GARAGE_PORT` or `PORT` env var, defaulting to port **4177**. Binds to `127.0.0.1` unless `PORT` is set, in which case it binds to `0.0.0.0`. Includes full API surface plus Ollama/MCP integrations. |
| `cloud-server.js` | Cloud (Railway) server. Listens on `PORT` env var, defaulting to **8080**. Stripped-down surface suitable for stateless cloud deployment. |

Both servers:
- Serve static UI from `apps/lantern-garage/public/`
- Expose a REST API under `/api/dream/*` (chat, journal entries)
- Write dream journal entries as append-only JSONL to `data/dream_journal/`
- Log request method and path to stdout only; no persistent access logs

### `surfaces/`

Static HTML surfaces served directly by GitHub Pages or the local server:

| Surface | Purpose |
|---|---|
| `index.html` | Root landing page |
| `shareholder-index/` | Shareholder packet surface |
| `garage/` | Tony Garage cockpit |
| `dashboard/` | Operator dashboard |
| `agent-fleet/` | Agent fleet monitor |
| `desktop/` | Lantern desktop shell |

### `skills/`

Operator skill definitions consumed by Claude Code and the agent harness.

`skills/super-jarvis-lantern-os/SKILL.md` is the canonical single entrypoint for all Lantern OS agent work. Legacy subskill folders under `skills/` remain as source references only.

### `data/`

Append-only JSONL ledgers stored on local disk. No database.

| Path | Contents |
|---|---|
| `data/dream_journal/` | Dream Journal entries (one `.jsonl` file per session or date) |
| `data/wallet/` | Wallet and cash ledger events |
| `data/world-model/` | Bayesian world-model belief state |

### `.github/workflows/`

| Workflow | Purpose |
|---|---|
| `ci.yml` | Continuous integration — lint, test, validate |
| `deploy.yml` | Deployment pipeline: GitHub Pages (static UI) + Railway (cloud server) |

---

## Data Flow

```
Browser
  └─► cloud-server.js  (Railway, PORT env var)
        ├─► GET  /api/dream/entries  →  reads  data/dream_journal/*.jsonl
        └─► POST /api/dream/chat     →  appends data/dream_journal/*.jsonl
                                         (optionally calls Claude API if
                                          ANTHROPIC_API_KEY is set)

Browser
  └─► server.js  (local, port 4177)
        ├─► same /api/dream/* routes
        ├─► /api/conversations, /api/operator-notes, etc.
        └─► local Ollama (if running) for offline AI replies
```

All persistent state lives in JSONL files on the host filesystem. There is no database, no cloud sync, and no background replication.

---

## Deployment Model

### Local

```
node apps/lantern-garage/server.js
# Listens on http://127.0.0.1:4177 by default
# Set LANTERN_GARAGE_PORT to override
```

### Cloud (Railway)

- Runtime: Node.js, auto-detected by Railway via Nixpacks
- Entry point: `apps/lantern-garage/cloud-server.js`
- Port: `PORT` environment variable (set by Railway at deploy time)
- Triggered by `deploy.yml` via Railway deploy hook on pushes to `master`
- JSONL data files are co-located on the Railway volume or ephemeral filesystem

### Static UI (GitHub Pages)

- Source: `apps/lantern-garage/public/` and `surfaces/`
- Published to the `gh-pages` branch via `peaceiris/actions-gh-pages`
- Triggered by `deploy.yml` on pushes to `master`
- Served at the repository's GitHub Pages URL

### AWS ECS

AWS ECS was retired in favor of Railway. The `deploy-aws.yml` workflow file remains for historical reference but is not part of the active deployment path.

---

## Key Design Constraints

- **No database.** All state is append-only JSONL on disk.
- **No cloud sync by default.** Data does not leave the device unless the operator explicitly exports it or deploys to Railway.
- **Offline-capable.** The local server runs without any network access; AI features fall back to local Ollama when `ANTHROPIC_API_KEY` is not set.
- **Static-first UI.** Surfaces are plain HTML/CSS/JS; no build step required for the frontend.
