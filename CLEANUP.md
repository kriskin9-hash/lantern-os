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

### 4. Docker Sprawl (In Progress)
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
- Move one-off handoff docs into `docs/archive/`
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

**Last Updated:** 2026-06-03