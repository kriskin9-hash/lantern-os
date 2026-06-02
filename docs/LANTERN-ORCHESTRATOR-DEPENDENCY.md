# Orchestrator Dependency Contract

## Status

**Current:** MCP rebuild in progress  
**Target:** All agent slots discoverable and dispatch-ready  
**Blocker:** Fleet rebuild required before live dispatch

---

## What This Means

The Lantern OS orchestrator (in `gm-agent-orchestrator` repo) manages a **named fleet** of AI agents:

- **Claude** — Reasoning and analysis
- **Codex** — Code review and implementation
- **Gemini** — Research and exploration
- **GPT** — General-purpose chat and iteration

Each agent slot must:
1. Register with the MCP server (Model Context Protocol)
2. Discover available tools (via `/tools/list` endpoint)
3. Bind to a specific operational context (e.g., "code review mode")
4. Remain callable by the operator (dispatch gate held until all ready)

---

## Current State

| Component | Status | Notes |
|-----------|--------|-------|
| MCP Server | Online (canary check required) | SSE transport, tool registry live |
| Claude slot | Pending re-registration | Awaiting MCP rebuild completion |
| Codex slot | Pending re-registration | Awaiting MCP rebuild completion |
| Gemini slot | Pending re-registration | Awaiting MCP rebuild completion |
| GPT slot | Pending re-registration | Awaiting MCP rebuild completion |
| Tool discovery | 42 tools pending | Available once slots are registered |
| Fleet dispatch | Held (founder-only) | Requires all slots to be discoverable |

---

## What "Stale Slots Are Not Available" Means

If an agent slot has not checked in with the MCP server within the **heartbeat window** (default: 30 seconds), it is considered **stale** and is removed from the dispatch pool.

**Why this matters:**
- Prevents hung agents from accepting work
- Ensures every dispatched task goes to a responsive agent
- Forces explicit re-registration after restarts

**Current state:** All slots are stale because the MCP rebuild deleted their registration state. This is expected and safe.

---

## How to Validate

Run the readiness test:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Test-LanternOrchestratorDependency.ps1
```

**Expected output (when ready):**
```
✓ MCP server responding
✓ All 4 agent slots registered
✓ Tool discovery working
✓ Stale slot cleanup functional
✓ Dispatch gate ready to unlock
Status: READY FOR DISPATCH
```

**Current output (rebuild in progress):**
```
✓ MCP server responding
✗ 0 of 4 slots registered (waiting for re-registration)
✗ Tool discovery incomplete (42 pending)
✓ Stale slot cleanup functional
✗ Dispatch gate locked (slots must register first)
Status: FLEET REBUILD IN PROGRESS
```

---

## Promotion Path

1. **Rebuild phase** (current)
   - MCP server running
   - Agent slots waiting for re-registration signal
   - Dispatch held (founder-only gate)

2. **Registration phase**
   - Codex script sends re-registration request to each slot
   - Slots check in with MCP server
   - Tool discovery begins

3. **Validation phase**
   - All slots appear in fleet roster
   - Tool registry is complete
   - Stale slot cleanup is working

4. **Dispatch ready** (final)
   - Operator can unlock dispatch gate
   - Fleet accepted work from Lantern chat
   - Tasks routed to available slots

---

## What Dispatch Means

When the dispatch gate unlocks, the operator can:

```
/dispatch "code review of src/foo.js"
```

The orchestrator will:
1. Find an available agent slot (Claude, Codex, Gemini, or GPT)
2. Send the task + MCP tool list
3. Let the agent choose tools and execute
4. Return results to operator

**Dispatch is founder-only** until:
- All slots are registered
- Tool registry is complete
- Three successful test dispatches are logged
- Operator explicitly approves for public use

---

## Key Implementation Details

**lantern-codex-impl:** The implementation lane where agent integration happens. Each agent (Claude, Codex, Gemini, GPT) has a corresponding directory with:
- Slot registration script
- Tool discovery handlers
- Heartbeat/keepalive logic
- Work queue processor

**mcp_ready_fleet_rebuild_required:** When true, the fleet must be rebuilt before dispatch resumes. This is a **safety gate**—it prevents stale agents from accepting work.

**canDispatchAgents:** When false, all dispatch requests return 403 Forbidden. Operator must explicitly set this to true after validation.

---

## Files Involved

- `.github/workflows/orchestration-challenge-ci.yml` — CI job validates fleet state
- `data/orchestrator-queue/` — Pending tasks (read-only for Garage)
- `manifests/orchestrator-dependency.json` — This readiness manifest
- `scripts/Test-LanternOrchestratorDependency.ps1` — Validation script
- `gm-agent-orchestrator/` — The actual orchestrator (separate repo)

---

## Rollback

If something goes wrong during rebuild:

1. Stop all agent processes
2. Delete `data/orchestrator-queue/` (safe—read-only copy in `gm-agent-orchestrator` repo)
3. Restart MCP server (`uvicorn src.mcp_server.server:app --port 8787`)
4. Re-run agent registration scripts
5. Validate with `Test-LanternOrchestratorDependency.ps1`

---

## Next Steps

1. Wait for MCP rebuild to complete
2. Agent slots will auto-register once rebuild signals them
3. Run validation script to confirm readiness
4. Operator approves dispatch unlock
5. Founder-only dispatch is live

**Do not manually unlock the dispatch gate.** The fleet must prove readiness first.
