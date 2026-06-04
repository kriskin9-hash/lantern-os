# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## P0 — Mandatory init gate (read before any tool call)

Before writing code, running commands, or editing files, you must read these in order:

1. `AGENTS.md` — root rules, branch policy, grudgebook protocol, work rules
2. `docs/agent-start-here.md` — safe workflow, evidence standard, final report shape
3. `docs/model-guides/claude.md` — Claude-specific execution style and validation order
4. `docs/agent-contract.md` — source-control closure, evidence records, done/blocked format
5. `docs/grudgebook.md` — standing corrective rules; read before every task

If you have not read all five files this session, stop and read them before proceeding.

This gate exists because skipping it has caused repeated branch policy violations, false confidence claims, and auth-mode errors. See grudgebook entry 2026-05-05.

---

## Repo purpose and boundaries

This repo owns local multi-agent orchestration: task queues, agent slots, worktrees, dashboard status, cross-repo priority reporting, and token/rate-limit recovery.

It does **not** own GameMaker gameplay (→ `ChildOfLevistus`) or room/object inspection tooling (→ `gamemaker-room-editor`).

## Service topology (immutable)

| Service | Port | Notes |
|---------|------|-------|
| Orch MCP server | `http://127.0.0.1:8787` | JSON-RPC at `/mcp`; SSE at `/mcp/sse`; health at `/health` |
| Dashboard | `http://127.0.0.1:8765` | Do not start manually; managed by `Ensure-OrchestratorDashboard.ps1` |

**Always check `http://127.0.0.1:8787/health` before reporting MCP server status.** A `{"error":"unauthorized"}` response means the server is up but unusable — not "working." A valid live response has `ok: true`.

## MCP server — local start (no auth)

```powershell
cd "$env:USERPROFILE\Documents\gm-agent-orchestrator"
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Start-OrchMcpServer.ps1 -NoAuth
```

Verify:
```powershell
Invoke-RestMethod http://127.0.0.1:8787/health | ConvertTo-Json
# expected: ok=true, noAuth=true
```

The `-NoAuth` flag is required for local use. Without it, all MCP tool calls return `{"error":"unauthorized"}`.

## Build / lint / test commands

```powershell
# Parser-check any edited .ps1 before committing
powershell -NoProfile -Command "
  \$errors = \$null
  [System.Management.Automation.Language.Parser]::ParseFile('<path>.ps1', [ref]\$null, [ref]\$errors)
  if (\$errors) { \$errors | ForEach-Object { Write-Error \$_ } } else { 'OK' }
"

# Run a targeted script test
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Test-OrchestratorTaskVisibility.ps1

# Fleet readiness check
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Test-AgentFleetReady.ps1
```

## Architecture

### Runtime flow

```
queue task
  -> slot claims task into tasks/active/
  -> worktree receives AGENT_RESUME.md + TASK_QUEUE.md
  -> agent starts on its feature branch
  -> output streamed to logs/
  -> status/<slot>.json updated
  -> agent commits, pushes, opens PR
  -> task moves to tasks/done/ or tasks/failed/
```

### Key scripts

| Script | Purpose |
|--------|---------|
| `scripts/Start-GmAgentOrchestrator.ps1` | Top-level launcher; reads `config/agents.json`, creates worktrees, starts slot runners |
| `scripts/Start-AgentSlot.ps1` | Claims one task, injects contract, runs agent command, handles resume loops |
| `scripts/New-AgentWorktree.ps1` | Creates one branch+worktree per agent slot |
| `scripts/Start-OrchMcpServer.ps1` | MCP JSON-RPC server; dots in `Start-OrchMcpServer.Tools.ps1` for tool dispatch |
| `scripts/Start-Dashboard.ps1` | Dashboard server (use `Ensure-OrchestratorDashboard.ps1` to manage, not this directly) |

### Config files

| File | Purpose |
|------|---------|
| `config/agents.json` | Slot definitions: name, agent type, role, branch, command templates |
| `config/slot-bindings.json` | Which slots are bound to which task owners |
| `config/local-services.json` | Local port/path overrides |
| `config/projects.json` | Repo paths for cross-repo work |

### Task queue layout

```
tasks/
  queue/    — pending work (claimed by slot runners)
  active/   — in-progress (owned by a running slot)
  done/     — completed with PR evidence
  failed/   — failed after one validation cycle
  hold/     — explicitly parked with reason
```

## Branch and worktree rules (enforced by Stop hook)

- **Always branch before the first edit.** Never edit on `master`.
- Branch naming: `feature/<issue>-<slug>`, `fix/<slug>`, `docs/<slug>`
- One active branch per workstream. Resolve current branch (push → PR → merge/close) before opening an unrelated one.
- The Stop hook at `.claude/hooks/enforce-pr-closure.ps1` blocks Claude from finishing a turn if the branch has unpushed commits or no open PR. It auto-pushes if auto-push is enabled.

## Grudgebook protocol

A grudge is a formal reliability event, not casual feedback. Before any task is marked done, append to `AGENT_LOG.md`:

```
Precheck: read GRUDGEBOOK.md for <task-filename>
```

Grudge entries live in `docs/grudgebook.md`. Do not erase them. They can only be marked addressed with corrective rules and evidence.

## Dashboard

- Source of truth for the web UI: `dashboard/index-v3.html`
- Do not edit `dashboard/index.html` directly — it is managed by the dashboard update script.
- If told "dashboard is corrupted," read the actual HTML file first before diagnosing.

## Final report format

```
Result: pass/fail/partial
Issue: #<number or none>
Branch: <branch>
Command: <exact command or not run>
Files changed: <short list>
Validation: <pass/fail/not run + reason>
Verified: <observable facts>
Assumed: <assumptions or none>
Grudgebook entry required: yes/no + reason
Next: <one action only>
```
