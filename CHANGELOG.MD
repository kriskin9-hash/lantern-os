# Changelog

All notable changes to Lantern OS are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/) conventions. Entries are grouped by release date. This project is local-first and private, so notes reflect what was verified locally.

## [1.2.5] - 2026-06-10

**Commit:** 1441d9e | **Branch:** master

### Testing & Validation

- API: 18/18 tests passing (create, stats, search, chat, stream, dashboard)
- Dream chat: Agent selection and three-doors validation working
- Landing page: Renders correctly with all CTA panels
- Journal page: Conversation interface and notepad functional
- Three-doors scenario: API returns contextual door suggestions
- Server: Hot-reload enabled on port 4177, Discord bot connected

### Data Updates

- Updated status-cube data model with validation results
- Updated dream-journal agent-slots manifest
- Refreshed settings and provider configuration
- Synced dependencies in package.json

---

## [1.2.4] - 2026-06-10

**Commit:** 04595fb | **Branch:** feat/slot-worker-pool

### Features

- SlotWorker pool implementation
- Health server for monitoring
- Daemon CLI for background tasks
- Convergence loop health checks

---

## [1.2.3] - 2026-06-10

**Commit:** 6082d54

### UI Updates

- RAG House page with technical architecture breakdown
- Status Cube visualization (4D axes: x/y/z/t)
- Tesseract Convergence Loop (20 phases)
- Convergence IO Engine diagram
- Agent Fleet design (36-slot architecture)
- Provider Chain visualization
- Knowledge center updated with RAG House link

---

## [1.2.2] - 2026-06-08

**Commit:** d8b05e3

### Maintenance

- Dependency synchronization
- Build configuration updates

---

## [1.2.1] - 2026-06-07

**Branch:** master

### Features

- `start:master` auto-sync: fetch → merge → push → HFF seed → start server
- Moon heartbeat indicator with drift-aware animation (9s cycle)
- Markdown renderer for `/repo/*.md` and `/repo/*.txt` files
- Human Flourishing Frameworks dashboard with 62 Bayesian beliefs
- Real-time 30s polling of belief updates

### Versioning

- `version.json`, root `package.json`, and garage `package.json` synced to 1.2.1

---

## [1.2.0] - 2026-06-07

**Category:** Major Release

### Startup & Autostart

- `Start-Lantern.ps1 -RegisterAutostart` registers Windows Task Scheduler
- Full boot sequence: `git pull origin master` → HFF seed → `node --watch`
- Unlimited crash-restart with 1-minute backoff
- Boot logs to `logs/lantern-autostart.log`

### Dream Chat UX

- Welcome message grounded in user context ("What's on your mind?")
- Default model: `qwen2.5-coder` via Ollama
- Fallback suggestions updated for gaming/rest/building context

### HFF Dashboard

- Removed Flask proxy; `/flourishing` reads `snapshot.json` directly
- WorldModel seeded from `seed_data.py` (62 beliefs, ~0.50 flourishing)
- HFF snapshot excluded from git (runtime-generated at boot)
- Route ordering fixed (no longer intercepted by catch-all)

### CI & Code Quality

- `slop-check.yml`: 5 parallel jobs (secrets, debug, OWASP, diff size, dupes)
- `anti-sprawl.yml`: root-level file detection refined
- `.clauderules` anti-slop ruleset committed
- Per-agent workstream hooks: one PR lane per agent prefix
- Slop gate in commit-msg hook

### Versioning

- `version.json`, root `package.json`, and garage `package.json` synced to 1.2.0
- Stale HTML version strings removed; version badge now reads `version.json` dynamically
