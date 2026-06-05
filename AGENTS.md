# AGENTS.md — Lantern OS

A focused guide for AI coding agents. **Read this before touching anything.**

**Core principle:** Be honest about what is real vs. designed. Never fabricate state.

---

## Token-Saving Contract (CRITICAL — read first)

This repo is designed for agentic-first workflows. Every agent (Claude, Gemini, Codex, Devin, Windsurf) burns tokens on context. The rules below exist to minimize waste.

### 1. Read the manifests before exploring the code

| File | What it tells you | Saves |
|------|------------------|-------|
| `data/pcsf/health.pcsf.json` | Every API endpoint, its expected response, pass/fail state | Don't curl to discover routes |
| `data/pcsf/provider.pcsf.json` | Which AI providers are configured, fallback chain order | Don't grep .env or stream-chat.js |
| `data/pcsf/model.pcsf.json` | Default model per provider, available overrides | Don't search for model strings |
| `data/pcsf/agent.pcsf.json` | All agents, their capabilities, route bindings | Don't explore routes/ to understand what exists |
| `data/pcsf/settings.pcsf.json` | Every env var, purpose, current presence state | Don't grep for process.env |
| `data/pcsf/narrator.pcsf.json` | All 6 persona narrators, keyword routing rules | Don't read dream-chat.js to understand agents |
| `manifests/dream-journal-v1-agent-slots.json` | Queued work items with priority + description | Don't ask "what's left to do" |

**Rule: Read the PCSF file first. Only touch source code if the manifest doesn't answer your question.**

### 2. Use the orchestrator instead of manual exploration

```bash
# Health check — is the server running? What's the state?
python src/convergence_io_engine.py health

# What needs fixing? Run the 12-phase convergence loop
python src/convergence_io_engine.py loop

# Ask the AI (uses Gemini/Claude via the provider chain)
python src/convergence_io_engine.py converge --message "what should I work on next" --persona keystone

# Inspect slots, metrics, circuits
python src/convergence_io_engine.py inspect
```

**Rule: Run `health` or `inspect` before reading source files. The orchestrator already knows the repo state.**

### 3. Delegate to non-Claude agents

Claude is expensive. Use it for design decisions and complex debugging. Delegate these to Gemini/Codex/local agents:

| Task type | Delegate to | Why |
|-----------|-------------|-----|
| Route wiring (1 file) | Gemini / Codex | Mechanical, well-defined |
| Test writing | Gemini / Codex | Pattern-match from existing tests |
| CSS/HTML tweaks | Any agent | Non-critical, fast iteration |
| PCSF file updates | Any agent | JSON edits, no logic |
| CSF ingestion docs | Any agent | Markdown, no code |
| `requirements.txt` edits | Any agent | One-line changes |

**Claude is for:** Orchestrator bugs, stream architecture, provider chain logic, system prompt design, security review.

### 4. Don't re-read files you've already read

The route architecture is modular. Each file handles one domain:

```
apps/lantern-garage/
  server.js              — 90 lines, just loads routes + deps
  routes/
    status.js            — /api/health, /api/status, wallet, readiness
    rag.js               — /api/rag-cache, flat-rag-house
    operator.js          — /api/operator-notes, conversations, actions
    files.js             — /repo/*, /view (markdown)
    dreamer.js           — /api/dreamer, /api/agents
    dream.js             — ALL /api/dream/* + /api/settings/providers
    surfaces.js          — /hub, /surfaces/*, static catch-all
  lib/
    stream-chat.js       — SSE streaming (Gemini→Claude→OpenAI→Grok→Ollama)
    dream-chat.js        — Non-streaming chat + persona selection
    dreamer-store.js     — readRecentDreams(), notebook storage
    conversation-store.js — append/read conversation JSONL
```

**Rule: If you need a route, read `routes/dream.js`. If you need streaming, read `lib/stream-chat.js`. Don't read `server.js` — it's just glue.**

### 5. Don't discover what tests exist — run them

```bash
node tests/test_dream_journal_api.js       # 18 API tests — requires running server
node tests/test_dream_chat_multiturns.js   # 11 multi-turn tests — requires running server
python -m pytest tests/test_dashboard_ux.py tests/test_dreamer_integration.py -q  # 26 Python tests
```

**Rule: Run tests, read failures. Don't glob for test files or read test code to understand what's covered.**

### 6. CSF ingestion docs ARE the task queue

```
csf/ingest/
  convergence-kvcache-compression.md    — FlowKV tiered history compression
  convergence-stable-diffusion-doors.md — Local SD image gen per door
  convergence-asmr-tts-chain.md         — ElevenLabs/OpenAI TTS provider chain
  convergence-conversation-tree.md      — Branch-per-door session tree
  convergence-model-training.md         — QLoRA fine-tune roadmap
  ROOT-DOCS-CONSOLIDATION.md            — Docs pending CSF ingest then delete
```

Each file has: problem, proposed implementation with code sketch, files to change, effort estimate. **Pick one and implement it — don't re-research what's already documented.**

---

## Quick Start

**Build & Test**
```bash
python -m pip install -r requirements.txt
node apps/lantern-garage/server.js &       # start server (background)
node tests/test_dream_journal_api.js       # 18/18 should pass
node tests/test_dream_chat_multiturns.js   # 11/11 should pass
```

**Run Locally**
```bash
node apps/lantern-garage/server.js          # port 4177
python src/mcp_server/server.py             # port 8771 (optional)
```

**Orchestrator**
```bash
python src/convergence_io_engine.py health  # server health
python src/convergence_io_engine.py loop    # 12-phase convergence check
```

---

## Real vs Design Contract (Critical)

**Real (have working implementations):**
- `dream_journal` — full CRUD, streaming chat, 5 providers, 3-doors canaries
- `lucid_dreaming` — lucidity tracking, technique logging, dream-sign flags
- `archive_curator` — CSF compression, JSONL export
- `voice_curator` — Web Speech STT/TTS in browser

**Design contract only (do not claim live):**
- All other `skills/*/SKILL.md` entries
- `super_jarvis_fleet` (36 slots, currently `activeSlots = 0`)
- `kalshi_bridge`

Never claim a skill or fleet slot is active unless confirmed by implementation or status file.

---

## Monoworkstream Rule (Single-Dev Workflow)

This repo enforces a **single workstream**: only one open PR at a time.

- **No new commits while any PR is open.** Finish the current PR (merge or close) before starting new work.
- **No new branches while any PR is open.** The pre-commit and pre-push hooks enforce this via GitHub CLI.
- **Emergency bypass:** `SKIP_MONOWORKSTREAM=1 git commit ...` or `SKIP_MONOWORKSTREAM=1 git push ...`

---

## Workspace Hygiene (Critical)

A clean workspace prevents context fragmentation and merge rot.

### Branch policy
- **Only `master` and `gh-pages` are long-lived branches.** All other branches are temporary.
- **Delete your branch immediately after merge.** The `branch-cleanup.yml` workflow auto-deletes merged PR branches.
- **Never reuse an old branch.** Always create a new branch from latest `master`.
- **Branch naming:** `<type>/<short-description>` (e.g., `feat/convergence-io-tier`, `fix/mcp-dotenv`).
- **Valid types:** `feat`, `fix`, `docs`, `chore`, `test`, `refactor`.

### Before starting work
```bash
# 1. Check for open PRs (monoworkstream)
gh pr list --state open

# 2. Ensure master is current
git checkout master
git pull origin master

# 3. Create a fresh branch
git checkout -b feat/your-feature-name
```

### After merging
```bash
# Delete local and remote branch
git push origin --delete feat/your-feature-name
git branch -D feat/your-feature-name

# Prune stale refs
git fetch --prune
```

### Forbidden branches (auto-deleted if found)
- `dev`, `rebase`, `merge-resolved-prs` — these are not part of the workflow.
- Any branch with garbage commits (e.g., "ai", "ay", "commit").
- Any branch older than 30 days that has been merged.

---

## Rules for AI Agents

1. **Read PCSF manifests before reading source code.**
2. Read the file before editing it.
3. Run relevant tests after changes.
4. **Never fabricate status** — only report measurable state.
5. Only register real implementations in `src/mcp_server/server.py`.
6. All changes should go through Pull Requests.
7. No new top-level directories without a ticket.
8. Never commit secrets (`.env` is gitignored).
9. Streaming uses `POST /api/dream/chat/stream` SSE endpoint (not GET).
10. **Respect monoworkstream** — check for open PRs before creating branches.
11. **Delegate mechanical work** to cheaper agents. Reserve Claude for architecture.
12. **Run the orchestrator** (`convergence_io_engine.py`) before exploring manually.

---

## Key File Locations

| What | Where |
|------|-------|
| Server entry | `apps/lantern-garage/server.js` (90 lines, loads routes/) |
| All dream routes | `apps/lantern-garage/routes/dream.js` |
| SSE streaming | `apps/lantern-garage/lib/stream-chat.js` |
| Dream chat UI | `apps/lantern-garage/public/dream-chat.html` |
| Landing page | `apps/lantern-garage/public/index.html` |
| Provider settings | `POST /api/settings/providers` in `routes/dream.js` |
| Orchestrator | `src/convergence_io_engine.py` |
| MemOS bridge | `src/convergence_io/memos_bridge.py` |
| PCSF state files | `data/pcsf/*.pcsf.json` |
| Work queue | `manifests/dream-journal-v1-agent-slots.json` |
| CSF task docs | `csf/ingest/*.md` |
| CI pipeline | `.github/workflows/ci.yml` |
| Cloud deploy | `apps/lantern-garage/cloud-server.js` (thin wrapper over server.js) |

**Last Updated:** 2026-06-05 — v1.0.0 Dream Journal Orion Edition