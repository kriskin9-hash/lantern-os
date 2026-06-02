# Suzie — Local-First AI Work Orchestrator

Windows-first control plane for supervising 1–40 AI agents across local worktrees, GitHub task queues, MCP tool boundaries, and provider quota state. Built for distributed foundry operations: 1 Founder + 20 trained operators across 20 PCs and 20 dedicated agent slots.

→ **[Foundry Master Plan](FOUNDRY-PLAN.md)** — org model, 22 product streams, revenue to $4M ARR, consent-bounded resource pool, cleanup phases

## What it does

- Coordinates multi-agent workflows across local + cloud providers
- Enforces MCP tool boundaries (safe-tool policy)
- Manages provider quota and fallback logic
- Maintains durable state via GitHub issues/PRs and local worktrees
- Operator UI dashboard with three-view contract

## Quick start

```powershell
Start-Dashboard.ps1
```

## Architecture

```
Operator
  ↓
Suzie orchestrator (PowerShell + Python)
  ├─ Task queue (queue → active → done/failed)
  ├─ Worktree isolation per agent slot
  ├─ MCP boundary (tool allowlist)
  ├─ Provider preflight + quota tracking
  └─ Dashboard three-view status UI
  ↓
Agent slots (Claude / Codex / Gemini / DeepSeek)
```

## License

[TBD — source-available + paid hosted tier]

---

**Status:** TRL 4 (lab-validated control plane)  
**Next:** [Read FOUNDRY-PLAN.md for full org model and stream catalog](FOUNDRY-PLAN.md)

ChildOfLevistus
  owns the actual game, game-specific contracts, and GameMaker project files
```

## Setup from Documents

After extracting this folder to `Documents`, run:

```powershell
cd "$env:USERPROFILE\Documents\gm-agent-orchestrator"
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Publish-PrivateRepo.ps1
```

Then initialize local config:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Initialize-LocalConfig.ps1
```

Edit:

```text
config\projects.json
config\agents.json
```

Start the orchestrator:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Start-GmAgentOrchestrator.ps1
```
