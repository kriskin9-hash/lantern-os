# Agent Handoff — 2026-05-28 12:49 UTC

## CRITICAL: What's running right now

### Lantern Garage (local chat surface)
- **URL**: http://127.0.0.1:4177
- **Process**: node (PID 12960)
- **Repo**: C:\tmp\lantern-os\apps\lantern-garage
- **Status**: RUNNING — all endpoints verified

### Agent Fleet (4 active)
| Slot | PID | Task Claimed | Priority |
|---|---|---|---|
| gemini-flash | 12464 | research-rag-evidence-map-for-founder-packet | P1 |
| gemini-main | 12280 | restore-orchestrator-agent-fleet-health | P0 |
| codex-main | 10856 | fix-and-test-lantern-script-safety-set | P0 |
| gpt-web | 7504 | converge-founder-needs-ordered-worklist | P0 |

### MCP Orchestrator
- **URL**: http://127.0.0.1:8787
- **Status**: HEALTHY
- **Queue**: 7 remaining (was 11, 4 claimed)

## What was done this session

1. **Fixed app.js Promise.all bug** — `refreshOperatorQueue()` now runs parallel without polluting destructured array
2. **Added operator queue panel** to Lantern Garage — shows orchestrator tasks + local notes, P0 sorted first, with quick-note form
3. **Committed**: `8c7676b feat: add operator queue panel with P0-sorted task+notes lane and RAG records` in lantern-os
4. **Set token policy** in agents.json: 60K per-task, 600K daily fleet, free-first routing
5. **Cleared worktree blockers** — committed stale AGENT_RESUME.md in gemini-flash, gpt-web, codex-main worktrees
6. **Cleared gemini preflight** — set recommendedNext=evaluate, mcpIssueDetected=false
7. **Loaded lantern-booter** — 16 files (PDFs + MD) at C:\Users\alexp\OneDrive\Desktop\lantern-booter
8. **Dispatched 4 agents** in parallel on queued work

## Key paths

| What | Path |
|---|---|
| Lantern OS repo | C:\tmp\lantern-os |
| Orchestrator | C:\Users\alexp\Documents\gm-agent-orchestrator |
| Agent config | gm-agent-orchestrator\config\agents.json (gitignored, local only) |
| Worktrees | C:\Users\alexp\Documents\agent-worktrees\{slot-name} |
| Queue tasks | gm-agent-orchestrator\tasks\queue\*.md |
| Active tasks | gm-agent-orchestrator\tasks\active\{slot}__{task}.md |
| Garage conversations | lantern-os\data\conversations\garage-conversations.jsonl |
| Operator notes | lantern-os\data\operator-notes\notes.jsonl |
| RAG cache | lantern-os\data\rag-intake\external-llm-web-cache\cache.jsonl |
| Lantern booter (drag-drop) | C:\Users\alexp\OneDrive\Desktop\lantern-booter |
| Old voice chat data | C:\Users\alexp\.lantern\state\convo-stream.jsonl |
| Gemini preflight | gm-agent-orchestrator\status\gemini-preflight.json |

## Known blockers for next agent

1. **claude-main API key invalid** — last log: 401 auth error with key ****qgAA. Don't dispatch claude-main until key is refreshed.
2. **operator-intake pre-commit hook missing** — `scripts/git-hooks/pre-commit-agent-identity.ps1` not found in worktree. Still has 3 dirty files.
3. **gemini-pro disabled** — slot disabled in agents.json, no worktree prepared.
4. **Render 404** — human-flourishing-frameworks.onrender.com /os and /art routes return 404 despite deploy showing "live". safe_app.py routes exist at lines 966, 972. Likely send_from_directory path issue in container.
5. **7 tasks still in queue** — after 4 agents finish their current tasks, redispatch them on remaining queue items.

## How to redispatch agents

```
# Via MCP tools:
mcp__filesystem__start_agent  slot: "gemini-flash"
mcp__filesystem__start_agent  slot: "gemini-main"
mcp__filesystem__start_agent  slot: "codex-main"

# Check status:
mcp__filesystem__get_agent_status
mcp__filesystem__get_queue_summary
mcp__filesystem__get_latest_agent_logs
```

## Routing policy (agents.json)

Free first: gemini-flash (tier 0) → gemini-main (tier 0) → gpt-web (tier 1, free if logged in) → codex-main (tier 2, metered) → claude-main (tier 3, most expensive, last resort)

## Lantern Garage API quick reference

| Endpoint | Method | What it does |
|---|---|---|
| /api/status | GET | System status (arc, wallet, readiness, controls) |
| /api/operator-queue | GET | Merged orchestrator tasks + local notes, P0 first |
| /api/operator-notes | POST | Add {text, priority} note |
| /api/conversations | GET/POST | Local conversation log |
| /api/rag-cache | GET/POST | RAG memory items |
| /api/flat-rag-house | GET | Full flat RAG house state |
| /api/actions/run-loop | POST | Run convergence loop |
| /api/actions/flat-rag-ingest | POST | Ingest repos into RAG |
