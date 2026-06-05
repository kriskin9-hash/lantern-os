# AGENTS.md -- Lantern OS

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

## Rules for AI Agents

1. Read the file before editing it.
2. Run relevant tests after changes.
3. **Never fabricate status** -- only report measurable state.
4. Only register real implementations in `src/mcp_server/server.py`.
5. All changes should go through Pull Requests.
6. No new top-level directories without a ticket.
7. Never commit secrets.
8. Streaming uses `/api/dream/stream` SSE endpoint.
9. **Inspect the GitHub issue tracker** (`gh issue list`) before starting work -- check for open tickets, active workstreams, and blockers. Do not duplicate existing work.

## Key Guardrails

- Use Pull Requests for changes
- Keep PRs small and reviewable
- Check open issues and PRs before starting new work

**Last Updated:** 2026-06-05
