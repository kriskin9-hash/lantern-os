# Lantern OS — Repo Hygiene & Cleanup Log

**Date:** 2026-06-03  
**Owner:** Keystone  
**Goal:** Reduce sprawl, improve maintainability, and document the cleanup process.

---

## Summary of Sprawl

The repository grew rapidly with many one-off scripts, handoff documents, deployment variants, and duplicated Docker configurations. This made navigation and maintenance difficult.

---

## Work Completed

### 1. AGENTS.md Cleanup
- Removed heavy operator workflow sections
- Removed Linear ticket enforcement language
- Focused the file on AI agent guardrails only
- Kept critical "Real vs Design Contract" section

### 2. Linear Ticket Gate Removal
- Deleted `.github/workflows/linear-ticket-gate.yml`
- Removed Linear references from `AGENTS.md`
- (Note: GitHub branch protection still requires manual removal of the status check)

### 3. Dream Journal V1.0.0 Foundation
- Created minimal `dream-chat-v1.html`
- Created `crystallization_engine.py`
- Created `memory_layer.py`
- Created `rp_bot.py` with strict provider mode
- Removed fallback/hardcoded response paths in streaming logic

### 4. Upgrade Lab Website
- Added `apps/lantern-garage/public/upgrade-lab.html`
- Linked it from the Dream Journal nav
- Kept the change inside the existing public deploy surface to avoid another top-level folder
- Framed cleanup as evidence-backed and reversible instead of broad deletion

### 5. Docker Sprawl (In Progress)
See section below.

---

## Docker Sprawl Status

### Current State (High Sprawl)
- Multiple Dockerfiles scattered across the repo
- Several docker-compose variants with overlapping purposes
- No single source of truth for containerization

### Files Identified
- Root level: `Dockerfile.*`, `docker-compose.*.yml`
- `ops/`: Multiple Discord bot Dockerfiles
- `services/`: Per-service Dockerfiles
- `src/`: Rust component Dockerfiles
- `integrations/`: Framework-specific Dockerfiles
- `apps/`: Lantern Garage Dockerfile
- `config/docker/`: Additional Dockerfile

### Recommended Consolidation Path
1. Keep only **one unified Dockerfile** per major service
2. Move all Dockerfiles into `docker/` or keep them co-located with their service
3. Standardize on `docker-compose.yml` + override files only
4. Archive or delete old deployment variants

---

## Next Cleanup Priorities
- Consolidate Docker configurations
- Audit `scripts/orchestration/` for dead scripts tied to archived integrations
- Audit `src/` and `services/` for dead code
- Enforce "no new top-level directories" going forward

## Anti-Sprawl Enforcement

Added `.github/workflows/anti-sprawl.yml` (2026-06-03):

- Blocks PRs with new top-level directories outside the approved list
- Limits new files to 25 per PR
- Limits new markdown files to 4 per PR
- Improved structure, output, and maintainability

This replaces the previous Linear-ticket + sprawl gate.

---

## 2026-06-04 Cleanup Batch

### Cache & Temp Files
- Deleted all `__pycache__/` directories recursively (~60 directories)
- Deleted all `.bak` and `.bak-*` files (7 files)
- Deleted test CSF duplicates in `data/` (4 files)
- Deleted weird filename artifacts in `integrations/gm-agent-orchestrator/` (2 files)

### Archive Moves
- `reports/` → `archive/reports-2026-06-04/` (65 items)
- `school-packets/` → `archive/school-packets-2026-06-04/` (9 items)
- `integrations/gm-agent-orchestrator/` → `archive/gm-agent-orchestrator-2026-06-04/` (459 items)
- `surfaces/bayesian-dashboard/`, `dashboard/`, `desktop/`, `garage/`, `lantern-desktop/`, `tony-garage/`, `windsurf-dev/` → `archive/surfaces-2026-06-04/`
- `manifests/evidence/` → `archive/manifests-evidence-2026-06-04/` (69 items)
- `manifests/validation/` → `archive/manifests-validation-2026-06-04/` (57 items)
- Root handoff docs (`00-PUSHED-TO-MASTER.md`, `00-START-HERE.md`, `CODEX-HANDOFF.md`) → `archive/root-cleanup-2026-06-04/`

### Docker Sprawl
- Deleted `ops/Dockerfile-discord-bot-v2` (versioned duplicate)
- Deleted `apps/lantern-garage/node_modules/` (committed dependency bloat)

### Integration Consolidation
- Extracted `tools/gpt-web-api/` from archived `gm-agent-orchestrator` to `services/gpt-web-api/`
- Updated `README.md` paths for GPT Web API and Discord bot

### Gitignore Fixes
- Fixed broken `* -v2*` / `* -v3*` patterns (spaces made them invalid)
- Added `.claude-plugin/`, `.vscode/`, `.windsurf/` to IDE artifacts section
- Consolidated duplicate `*.tmp`, `*.log`, `__pycache__/` entries

---

**Last Updated:** 2026-06-04
