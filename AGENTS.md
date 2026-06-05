# AGENTS.md — Lantern OS

A focused guide for AI coding agents.

**Core principle:** Be honest about what is real vs. designed. Never fabricate state.

## Quick Start

**Build & Test**
```bash
python -m pip install -r requirements.txt
python -m pytest tests/ -q --tb=short --ignore=tests/test_anti_entropy_memory.py --ignore=tests/test_audit_chain.py --ignore=tests/test_discord_bot.py --ignore=tests/test_discord_voice_gate.py
```

**Run Locally**
```bash
node apps/lantern-garage/server.js          # port 4177
python src/mcp_server/server.py             # port 8771
```

## Real vs Design Contract (Critical)

**Real (have working implementations):**
- `dream_journal`
- `lucid_dreaming`
- `archive_curator`
- `voice_curator`

**Design contract only (do not claim live):**
- All other `skills/*/SKILL.md` entries
- `super_jarvis_fleet` (36 slots, currently `activeSlots = 0`)
- `kalshi_bridge`

Never claim a skill or fleet slot is active unless confirmed by implementation or status file.

## Monoworkstream Rule (Single-Dev Workflow)

This repo enforces a **single workstream**: only one open PR at a time.

- **No new commits while any PR is open.** Finish the current PR (merge or close) before starting new work.
- **No new branches while any PR is open.** The pre-commit and pre-push hooks enforce this via GitHub CLI.
- **Emergency bypass:** `SKIP_MONOWORKSTREAM=1 git commit ...` or `SKIP_MONOWORKSTREAM=1 git push ...`
- **Install hooks:** `powershell -ExecutionPolicy Bypass -File scripts/Install-MonoworkstreamHooks.ps1`

Rationale: as a solo dev, open PRs represent unfinished work. Starting a new branch before closing the old one fragments context and increases merge risk. The rule keeps the pipeline linear.

## Rules for AI Agents

1. Read the file before editing it.
2. Run relevant tests after changes.
3. **Never fabricate status** — only report measurable state.
4. Only register real implementations in `src/mcp_server/server.py`.
5. All changes should go through Pull Requests.
6. No new top-level directories without a ticket.
7. Never commit secrets.
8. Streaming uses `/api/dream/stream` SSE endpoint.
9. **Respect monoworkstream** — check for open PRs before creating new branches or commits.

## Key Guardrails

- Use Pull Requests for changes
- Keep PRs small and reviewable
- One open PR at a time (monoworkstream)

**Last Updated:** 2026-06-05