# Convergence Loop + CI/CD + Batch Framework (Integrated)

**Date:** 2026-06-02  
**Status:** Active  
**Architecture:** Closed-loop mutual validation

---

## Overview

Lantern OS now runs a **single unified system** where:
- **CI/CD validates the batch framework** (on every push to master)
- **Batch jobs validate CI/CD** (on every scheduled run)
- **Convergence loop orchestrates both** (source of truth for system readiness)

This is NOT separate systems — it's one integrated loop where each validates the other.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  CONVERGENCE LOOP (Source of Truth)                         │
│  Invoke-LanternConvergenceLoop-Enhanced.ps1                 │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  PHASE 1: CI/CD Validation                                  │
│  ├─ Check workflows exist (.github/workflows/ci.yml, etc)   │
│  ├─ Verify critical files (README, AGENTS, docs)            │
│  └─ Status: CICD_READY or CICD_BROKEN                       │
│                                                              │
│  PHASE 2: Batch Framework Validation                        │
│  ├─ Check batch config (config/batch-jobs-enhanced.json)    │
│  ├─ Verify all job scripts exist                            │
│  └─ Status: BATCH_READY or BATCH_BROKEN                     │
│                                                              │
│  PHASE 3: Mutual Validation Test                            │
│  ├─ If CICD_READY + BATCH_READY → MUTUAL_VALIDATION_ON     │
│  └─ Status: MUTUAL_ENABLED or MUTUAL_BLOCKED               │
│                                                              │
│  PHASE 4: Asset Discovery                                   │
│  ├─ Count skills, docs, workflows                           │
│  └─ Track changes                                           │
│                                                              │
│  PHASE 5: Report Generation                                 │
│  └─ Save receipt to manifests/evidence/                     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
         ↑                                        ↑
         │                                        │
         │ Triggered by               Validates  │
         │ schedule (batch)              and     │
         │ or manual (user)          informs     │
         │ or CI/CD (on push)                    │
         │                                        │
    ┌────┴────────────────────────────────────────┴─────┐
    │                                                     │
    v                                                     v
┌──────────────────────────┐      ┌──────────────────────────┐
│  BATCH FRAMEWORK         │      │  CI/CD PIPELINE          │
│  (Scheduled Jobs)        │      │  (Push-Triggered)        │
├──────────────────────────┤      ├──────────────────────────┤
│                          │      │                          │
│ config/batch-jobs-       │      │ .github/workflows/       │
│ enhanced.json            │      │ ci.yml                   │
│ (10 jobs, 8 groups)      │      │ (6 parallel jobs)        │
│                          │      │                          │
│ Groups:                  │      │ Jobs:                    │
│ • health (10min)         │      │ • validate-repo          │
│ • validation (30min)     │      │ • test-python            │
│ • core (1440min)         │      │ • test-node              │
│ • evidence (1440min)     │      │ • convergence-check      │
│ • discovery (2880min)    │      │ • integration-checks     │
│ • publish (4320min)      │      │ • convergence-loop-      │
│ • purge (4800min)        │      │   validation             │
│ • reports (10080min)     │      │                          │
│                          │      │ GATE: all-checks (pass?) │
│                          │      │                          │
│ Trigger: Orchestrator    │      │ Trigger: Push to master  │
│ (local schedule)         │      │ (automatic)              │
│                          │      │                          │
└──────────────────────────┘      └──────────────────────────┘
    │                                  │
    │ Runs validate-cicd.ps1           │ Runs convergence-loop-
    │ (checks CI/CD health)            │ validation job
    │ (checks batch is working)        │ (checks batch is working)
    │                                  │
    └──────────────────────────────────┘
              (Cross-validation)
```

---

## Trigger Model (Scheduled Only)

**KEY: This system ONLY runs on explicit triggers.** No infinite loops.

### Trigger Points

| Trigger | What Runs | When | Why |
|---------|-----------|------|-----|
| **Push to master** | CI/CD pipeline | Automatically | Validates code + batch framework |
| **Batch schedule** | Convergence loop + batch jobs | On configured intervals | Validates CI/CD + runs maintenance |
| **Manual user** | Either system | `./scripts/Invoke-LanternConvergenceLoop-Enhanced.ps1` | Operator debugging/validation |

### No Infinite Loops

- CI/CD **does not trigger** batch jobs
- Batch jobs **do not trigger** CI/CD
- Both **validate each other** but don't execute each other
- Safe cross-checks only (read-only validation)

---

## Batch Job Schedule

```
Every 10 min   → health-check (basic readiness)
Every 30 min   → validate-cicd (checks CI/CD exists + works)
Every 30 min   → validate-batch-framework (CI/CD checks batch config)
Every 60 min   → test-mutual-validation (both systems test each other)
Every 1 day    → convergence-loop (daily reconciliation)
Every 1 day    → loop-receipt (daily audit trail)
Every 2 days   → asset-discovery (scan for new skills/docs)
Every 3 days   → sync-rag-pdf (publish RAG + PDFs)
Every 3+ days  → post-ingestion-purge (cleanup old receipts)
Every 7 days   → generate-confidence-report (operator summary)
```

**Execution:** Orchestrated by `Invoke-AutomationOrchestrator.ps1` (local Windows machine)

---

## CI/CD Workflow

```
Push to master
    ↓
[CI Workflow] (6 parallel jobs + 1 convergence validation)
    ├─ validate-repo (files, manifests)
    ├─ test-python (pytest)
    ├─ test-node (Playwright)
    ├─ convergence-check (contract)
    ├─ integration-checks (cloud mirrors)
    └─ convergence-loop-validation ← NEW (validates batch framework)
    ↓
[all-checks] gate (did everything pass?)
    ↓
If green: [Deploy Workflow] triggers
    ├─ Docker build + validate health endpoint
    └─ Push to AWS ECS (Fargate)
```

---

## Mutual Validation Contract

### CI/CD → Batch Framework

**What CI/CD checks:**
1. ✓ `config/batch-jobs-enhanced.json` exists
2. ✓ JSON is valid
3. ✓ Schema has required fields: schema, jobs, groups, defaults
4. ✓ All job scripts referenced in config exist
5. ✓ Batch job directories are writable (can create logs/receipts)

**When:** Every push to master (happens in `convergence-loop-validation` job)

---

### Batch Framework → CI/CD

**What batch jobs check:**
1. ✓ `.github/workflows/ci.yml` exists and is valid
2. ✓ `.github/workflows/deploy.yml` exists and is valid
3. ✓ Critical files present (README.md, AGENTS.md, docs/CONVERGENCE-LOOP.md)
4. ✓ Dockerfile exists (needed for deploy job)
5. ✓ Health endpoint is defined in code

**When:** Every 30 minutes (via `validate-cicd` batch job)

---

## Evidence Trail

Both systems generate **receipts** (JSON logs) for audit:

```
manifests/evidence/
├─ convergence-20260602-093022.json    (Convergence loop run)
├─ cicd-validation-20260602-093522.json (Batch validates CI/CD)
├─ batch-validation-20260602-100022.json (CI/CD validates batch)
└─ mutual-validation-20260602-101022.json (Both systems working together)
```

Each receipt contains:
- Timestamp
- Trigger (batch | user | cicd)
- Phase results (CI/CD ready? Batch ready? Mutual enabled?)
- Assets discovered
- Errors and warnings

---

## Deployment Gates

```
Master commit
    ↓
CI passes?
    ├─ NO → Stop, fix issues, retry push
    └─ YES → Deploy gate unlocked
           ↓
        [Deploy] → Docker build + AWS ECS update
           ↓
        Cloud live ✓
```

---

## Example: Daily Operation

**8:00 AM:** Operator pushes to master
```bash
git push origin master
```
↓ CI runs (~5 min) → all-checks pass → Deploy runs (~3 min)
↓ **9:00 AM:** Lantern Garage + Central Hub live on AWS

**Every 10 min:** Health check runs (basic pulse)

**Every 30 min:** Batch job validates CI/CD is healthy
```
[validate-cicd] → Checks .github/workflows/ exists
```

**Every 1 day:** Full convergence loop runs
```
[Invoke-LanternConvergenceLoop-Enhanced.ps1]
├─ PHASE 1: CI/CD ready? YES ✓
├─ PHASE 2: Batch ready? YES ✓
├─ PHASE 3: Mutual validation? ENABLED ✓
├─ PHASE 4: Assets discovered: 5 skills, 20 docs, 2 workflows
└─ PHASE 5: Receipt saved → manifests/evidence/convergence-*.json
```

**Result:** System is healthy, no manual intervention needed.

---

## How to Run Manually

**Check system status now:**
```powershell
cd /path/to/lantern-os
.\scripts\Invoke-LanternConvergenceLoop-Enhanced.ps1 -Trigger "user"
```

Output shows:
- CI/CD ready? ✓/✗
- Batch ready? ✓/✗
- Mutual validation? ENABLED/BLOCKED
- Assets discovered
- Any errors/warnings

**Run a specific batch job:**
```powershell
# Validate CI/CD (batch job perspective)
.\scripts\Validate-CicdPipeline.ps1

# Validate batch framework (CI/CD perspective)
.\scripts\Validate-BatchFramework.ps1
```

---

## Configuration

**Batch jobs:** `config/batch-jobs-enhanced.json`
- Each job has: id, name, script, interval, group, priority, runAfter
- All intervals are in minutes (10 = every 10 min, 1440 = daily, etc)
- `runAfter` creates dependencies (wait for job X before running job Y)
- `failurePolicy`: "log" (continue) or "warn" (alert operator)

**CI/CD:** `.github/workflows/ci.yml` + `deploy.yml`
- All checks run in parallel (fast)
- Deploy only runs if CI passes
- No circular dependencies

**Convergence:** `Invoke-LanternConvergenceLoop-Enhanced.ps1`
- Source of truth for system readiness
- Can be triggered by batch, user, or CI/CD
- Runs 5 phases: CI/CD validation → Batch validation → Mutual test → Asset discovery → Report

---

## Safety Rails

✓ **No infinite loops:** CI/CD doesn't trigger batch, batch doesn't trigger CI/CD  
✓ **Clear triggers only:** Push (CI), schedule (batch), manual (user)  
✓ **Evidence trail:** Every run generates a dated JSON receipt  
✓ **Graceful degradation:** If one system fails, the other continues  
✓ **Operator control:** Can pause jobs, review evidence, make decisions  

---

## Future Enhancements

1. **Real-time monitoring:** Dashboard showing last convergence result
2. **Slack/Discord alerts:** Notify on mutual validation failures
3. **Auto-remediation:** If batch job fails, auto-run diagnostic script
4. **Predictive gates:** Use past convergence data to predict failures
5. **Cross-repo validation:** Extend to validate linked repos (windows-terminal, etc)

---

## Questions for Operators

1. What's the tolerance for deployment frequency? (Daily? Per-push? Weekly?)
2. Should batch jobs be pausable from a UI dashboard?
3. Who gets notified if mutual validation breaks?
4. How long should receipts be retained? (Currently: 30 per class)
