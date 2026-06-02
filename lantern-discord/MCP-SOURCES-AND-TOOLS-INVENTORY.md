# MCP Inventory: Lantern OS + Orchestrator Sources

**Date:** 2026-05-31  
**Scope:** Complete MCP tool catalog from all visible source repositories  
**Status:** Pre-v1.0.0 staging (Lantern OS convergence target)

---

## Overview: MCP Architecture

The orchestrator uses a **two-tier MCP strategy**:

1. **Public MCP** (gamemaker-mcp) — GameMaker tools usable by any developer
2. **Private Orchestrator MCP** — Multi-agent orchestration, task queue, agent coordination

Both repos use **HTTP JSON-RPC** endpoints with bearer token authentication.

---

## 1. PRIVATE ORCHESTRATOR MCP TOOLS

**Endpoint:** `http://127.0.0.1:8788/mcp` (port 8788, separate from orchestrator port 8787)  
**Auth:** Bearer token (stored in orchestrator config)  
**Source:** `C:\Users\alexp\Documents\gm-agent-orchestrator`

### A. Agent & Fleet Status (Read-Only)

| Tool | Purpose | Input | Output |
|------|---------|-------|--------|
| `get_agent_status` | Fleet availability, current tasks | None | JSON: agent slots, availability, task assignment |
| `get_queue_summary` | Task queue status | None | JSON: queue/active/hold/done/failed counts |
| `get_recent_failures` | Failed task audit trail | None | JSON: failed tasks with blockers |
| `get_latest_agent_logs` | Execution logs from all agents | None | JSON: timestamped log tails per slot |
| `get_agent_status` | Current task assignments | None | JSON: online/offline status, PIDs, task ETA |

### B. Repository & Git Management (Read-Write)

| Tool | Purpose | Input | Output |
|------|---------|-------|--------|
| `sync_repository` | Fast-forward sync (orchestrator repo only) | branch, remote | JSON: sync result, new HEAD |
| `get_branch_status` | Current branch + PR metadata | None | JSON: branch, commits, PR#, PR status |
| `get_github_issues_cached` | Cached GitHub issues (workaround) | None | JSON: issue list with state |
| `get_github_pr_status_cached` | Cached PR metadata (workaround) | None | JSON: PR list with checks |

### C. Task Queue Management (Read-Write)

| Tool | Purpose | Input | Output |
|------|---------|-------|--------|
| `requeue_task` | Move task from failed back to queue | task_path, reason | JSON: success, new task state |
| `fail_task` | Move task from active to failed | task_path, reason | JSON: success, failure record |
| `complete_task` | Mark task as done | task_path, reason | JSON: success, completion record |

### D. Agent Lifecycle (Read-Write)

| Tool | Purpose | Input | Output |
|------|---------|-------|--------|
| `start_agent` | Wake agent in a slot | slot, task_name, task_path | JSON: agent PID, start time |
| `rerun_agent` | Re-execute agent on same task | slot, task_name, task_path | JSON: rerun status |

### E. GameMaker Build Status (Read-Only, delegates to Public MCP)

| Tool | Purpose | Input | Output |
|------|---------|-------|--------|
| `get_gamemaker_project_info` | Project metadata | project name | JSON: name, version, platforms |
| `get_gamemaker_compiler_errors` | Parse compiler output | project name | JSON: error list, line numbers, severity |
| `get_sprite_asset_status` | Asset validation | project name | JSON: sprite counts, frame issues |
| `get_room_editor_status` | Room layout validation | project name | JSON: room structure, object placement |
| `get_game_build_status` | Aggregated build status | project name | JSON: build state, errors, warnings |

---

## 2. PUBLIC MCP TOOLS (GameMaker)

**Repository:** https://github.com/alex-place/gamemaker-mcp (planned, not yet public)  
**Visibility:** Public, for any GameMaker developer  
**Current Status:** Design phase (specs in `mcp-repo-split.md`)

### Planned Tools

| Tool | Purpose | Stability |
|------|---------|-----------|
| `get_gamemaker_project_info` | Project metadata (name, version, target platforms) | HIGH — stable format |
| `get_gamemaker_compiler_errors` | Parse compiler output, return structured list | HIGH — stable compiler output |
| `get_sprite_asset_status` | Validate sprites, frame counts, dimensions | HIGH — stable asset format |
| `get_room_editor_status` | Room layout, object placement validation | MEDIUM — custom tool |
| `get_script_analysis` | Static analysis: undefined vars, dead code | HIGH — pure parsing |
| `get_resource_dependency_graph` | Script dependencies, room→sprite relationships | HIGH — pure parsing |
| `get_gamemaker_version_info` | Installed GM version, extensions, runtime | HIGH — stable registry |

**Deployment Model:** NPM package `@gamemaker-tools/mcp` (planned)

---

## 3. HUMAN-FLOURISHING-FRAMEWORKS SERVICES

**Source:** `C:\tmp\human-flourishing-frameworks-scan`  
**Status:** TRL 4 (functional Flask + dashboard, kids edition TRL 2)  
**Live URLs:**
- Dashboard: https://human-flourishing-frameworks.onrender.com/
- Lantern OS Dashboard: https://human-flourishing-frameworks.onrender.com/os
- Health API: https://human-flourishing-frameworks.onrender.com/health
- System Status: https://human-flourishing-frameworks.onrender.com/api/status

### HFF Framework API Endpoints (Not traditional MCPs, but relevant to Lantern OS)

| Endpoint | Purpose | Auth | Use |
|----------|---------|------|-----|
| `GET /health` | Health probe | None | Liveness check |
| `GET /api/status` | System status | None | Current state snapshot |
| `GET /api/violations/compas` | COMPAS analysis summary | None | Audit/fairness reference |
| `POST /api/adoption/register` | Node liveness telemetry | Bearer token (adoption) | Mesh network registration |
| `GET /api/adoption/stats` | Adoption statistics | None | Fleet visibility |
| `GET /api/adoption/nodes` | Recent visible nodes | None | Node discovery |
| `POST /api/autonomous/submit` | Submit evidence for processing | Bearer token (write) | Agent escalation |
| `GET /api/autonomous/status` | Agent system status | None | Agent health |
| `GET /api/autonomous/audit` | Audit trail with chain verification | None | Compliance trail |
| `GET /api/world/status` | World model status | None | Beliefs snapshot |
| `GET /api/world/beliefs` | Current beliefs (filterable) | None | Measurement state |
| `GET /api/world/flourishing` | Flourishing scores by scope | None | Metric snapshot |
| `POST /api/world/observe` | Submit sensor measurements | Bearer token (write) | Telemetry ingest |
| `GET /api/world/corrections` | Model self-correction history | None | Audit trail |
| `GET /api/world/discover` | Anomalies and discovered patterns | None | Pattern detection |

**Token Types:**
- `HFF_WRITE_TOKEN` — Privileged writes (state changes, observations)
- `HFF_ADOPTION_ACCEPT_TOKEN` — Adoption telemetry (node liveness)
- `HFF_ADOPTION_SYNC_TOKEN` — Reporting node sync (telemetry posting)

---

## 4. LANTERN OS CONVERGENCE INTEGRATION

**Repository:** https://github.com/alex-place/lantern-os (remote, private staging)  
**Local Staging:** `C:\tmp\lantern-discord` (user's selected workspace)  
**Status:** Pre-v1.0.0 convergence loop validation

### Convergence Target

Lantern OS v1.0.0 is the **clean convergence point** for:
- Windows local-first surfaces
- NixOS deployment
- COMET LEAP management (foundry org model)
- Household AI surfaces
- GameMaker orchestration (`child-of-levistus` game)

### Shareholder Repos (Authority Sources)

| Repo | Purpose | Convergence Role |
|------|---------|------------------|
| `gm-agent-orchestrator` | Multi-agent coordination, task queue, MCP server | Core orchestration engine |
| `human-flourishing-frameworks-scan` | Lantern chat, media curator, HFF world model | User-facing surfaces + telemetry |
| `lantern-os` (remote) | v1.0.0 release control plane | Unified release container |

**Convergence Loop:** See `C:\tmp\human-flourishing-frameworks-scan\docs\CONVERGENCE-LOOP.md`

**Promotion Rule:** Nothing becomes v1.0.0 merely because it exists elsewhere. Promotion requires:
1. Running the convergence loop
2. Fixing the first 2–4 blocking issues
3. Explicit operator approval

---

## 5. HOW TO LOAD THESE MCPS

### Option A: Load Orchestrator MCP (Private)

**Prerequisites:**
- Windows 10/11
- PowerShell 7+
- Orchestrator repo in `C:\Users\alexp\Documents\gm-agent-orchestrator`

**Command:**
```powershell
cd C:\Users\alexp\Documents\gm-agent-orchestrator
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Start-OrchMcpServer.ps1
```

**Verify:**
```powershell
# MCP server should be listening on port 8788
curl -H "Authorization: Bearer $(cat config/mcp-bearer-token.txt)" `
  http://127.0.0.1:8788/mcp
```

**Integration:** Once running, Claude agents can call any tool in the orchestrator MCP list above.

### Option B: Load Public MCP (GameMaker, when available)

**Status:** Not yet published. When ready:

```bash
npm install @gamemaker-tools/mcp
# or
pip install gamemaker-mcp  # Python FastMCP version
```

### Option C: Use HFF Framework APIs (No MCP, direct HTTP)

**Live Example:**
```bash
curl https://human-flourishing-frameworks.onrender.com/health
```

**Bearer Token Headers (for writes):**
```bash
curl -H "Authorization: Bearer <HFF_WRITE_TOKEN>" \
  -X POST https://human-flourishing-frameworks.onrender.com/api/world/observe \
  -d '{"sensor": "test", "value": 42}'
```

---

## 6. PORT LAYOUT (LOCAL ORCHESTRATOR)

| Port | Service | Purpose | Status |
|------|---------|---------|--------|
| 8765 | Dashboard UI | Ops overview + health reporting | Running (Lantern OS) |
| 8787 | Orchestrator control plane | Task queue, agent lifecycle | Running |
| 8788 | MCP JSON-RPC server | Claude agent tool access | Running (separate port) |
| 9001 | Dashboard (alt) | Legacy dashboard port | Optional |

**Historical Incident:** Port 8787 and 8788 collision was fixed in disaster-recovery documentation. MCP server must run on separate port from orchestrator.

---

## 7. SECURITY & TOKEN MANAGEMENT

### Bearer Token Rotation

Rotate tokens in these files:
- `config/mcp-bearer-token.txt` (orchestrator MCP)
- `config/agents.json` → each agent's provider tokens
- `.env` or environment variables for HFF tokens

**Never commit:**
- Bearer tokens
- API keys
- Credentials
- Full logs with secrets

### Safe-Tool Policy (GRUDGEBOOK)

All MCP tools are **read-only** unless explicitly marked as write:
- ✅ All get_* tools are read-only (no mutations)
- ✅ Stage/commit/mutation tools require explicit agent approval
- ✅ Task queue operations are audited with reason field
- ❌ No tools execute shell commands directly (use scripts)
- ❌ No tools delete data permanently

---

## 8. MCP PHASE ROADMAP

### Phase 1: Quick-Win Exposure (2-4 hours)
**Timeline:** Week 1  
**Owner:** Claude + Codex  
**Scope:** Wire 5 existing scripts as MCP tools (no new implementations)

1. `get_branch_status` — Git branch + PR lookup
2. `get_queue_summary` — Task counts
3. `get_token_budget_status` — Provider quota
4. `get_agent_status` — Fleet health
5. `get_game_build_status` — GameMaker build state

**Status:** Design phase (see `mcp-quick-wins-phase-1.md`)

### Phase 2: Strategic Tools (6-8 hours)
**Timeline:** Week 2  
**Scope:** Implement 5 new tools (requires design)

1. `stage_git_files` — Stage without UI
2. `commit_git_changes` — Commit with audit trail
3. `propose_queue_mutation` — Dry-run mutations
4. `get_stale_branch_list` — Branch cleanup
5. `run_safe_powershell` — Pre-approved script sandbox

---

## 9. VALIDATION CHECKLIST

- [ ] **Orchestrator MCP running:** `curl http://127.0.0.1:8788/mcp` returns 200
- [ ] **Bearer token valid:** No 401 auth errors
- [ ] **HFF services reachable:** Dashboard and API endpoints respond
- [ ] **Convergence loop docs readable:** `CONVERGENCE-LOOP.md` present
- [ ] **GameMaker project accessible:** `child-of-levistus` build can be checked
- [ ] **Agent slots available:** At least 1 agent slot idle for new work
- [ ] **Lantern OS v1.0.0 gate active:** No blocking issues in convergence loop

---

## 10. CONTACTS & REFERENCES

| Document | Location | Purpose |
|----------|----------|---------|
| Orchestrator README | `gm-agent-orchestrator/README.md` | System overview |
| Foundry Master Plan | `gm-agent-orchestrator/FOUNDRY-PLAN.md` | Org model, revenue, 22 streams |
| MCP Repo Split | `gm-agent-orchestrator/docs/.../mcp-repo-split.md` | Public vs. private MCP boundaries |
| MCP Quick Wins | `gm-agent-orchestrator/docs/.../mcp-quick-wins-phase-1.md` | Phase 1 tool exposure plan |
| HFF README | `human-flourishing-frameworks-scan/README.md` | Lantern + frameworks overview |
| Convergence Loop | `human-flourishing-frameworks-scan/docs/CONVERGENCE-LOOP.md` | v1.0.0 promotion criteria |
| Lantern OS Portal | `lantern-os` (remote) | Release control plane (private) |

---

**Status:** MCP infrastructure is **partially deployed and in Phase 1 design**.  
**Next Steps:** Execute Phase 1 quick-win exposure, then validate HFF integration for Lantern OS v1.0.0 release.
