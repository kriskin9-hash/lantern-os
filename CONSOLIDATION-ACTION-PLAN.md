# Dashboard Consolidation Action Plan

**Directive**: Single unified surface consolidation at https://lantern-os-cloud.netlify.app/
**Approved**: 2026-05-31
**Operator**: Alex Place

## Consolidated Surface

**Primary URL**: https://lantern-os-cloud.netlify.app/

Features:
- Main: Dream Journal AI ↻ Convergence2
- System: Batch Jobs, Health Check, Repositories
- Publish: RAG/PDF Sync, Agent Fleet
- Evidence: Arc Reactor, Run Receipts
- Held: 6 blocked items (operator approval required)

Status: No auto-execute · Human gate active

---

## Surfaces to Remove / Archive

### 1. Legacy Jupyter Notebooks
**Location**: Various `.ipynb` files in repo
**Action**: Archive to `artifacts/deprecated-notebooks/`
**Rationale**: All notebook functionality → Dashboard Evidence/Run Receipts
**Status**: PENDING

### 2. Static HTML Reports (Jekyll)
**Location**: `_site/` outputs, Jekyll config
**Action**: Archive to `artifacts/deprecated-reports/`
**Rationale**: Report generation → Dashboard Publish section
**Status**: PENDING

### 3. Separate GitHub Pages Views
**Location**: GitHub Pages secondary dashboards
**Action**: Consolidate functionality into Dashboard System/Health Check
**Rationale**: Single source of truth for repo status
**Status**: PENDING

### 4. COMET LEAP Surface PDFs
**Location**: Previously generated Orion PDFs (9 reports)
**Action**: Catalog in Dashboard Evidence/Run Receipts
**Rationale**: All output flows through Dashboard
**Status**: PENDING
**Files affected**:
- ADS-ARCHITECTURE-REVIEW-v0.1.pdf
- ALEX-PLACE-FOUNDER-ALL-STREAMS-CONVERGENCE-2026-05-27.pdf (4 variants)
- ALEX-PLACE-FOUNDER-REAL-PASS-2026-05-27.pdf
- ALEX-PLACE-GITHUB-REPO-SCAN-2026-05-30.pdf
- Plus 6 additional specialized reports

### 5. Email-based Asynchronous Reports
**Location**: Report delivery scripts, scheduled tasks
**Action**: Remove push-based reporting; Dashboard is pull-based operator-gated
**Rationale**: Operator queries Dashboard on-demand, no background email spam
**Status**: PENDING

### 6. Local Dev Dashboards
**Location**: Separate development-mode views
**Action**: Consolidate into Dashboard System/Batch Jobs (local execution context)
**Rationale**: Single interface for all execution contexts
**Status**: PENDING

### 7. External Monitoring Tool Dependencies
**Location**: Netlify UI, GitHub UI direct usage
**Action**: All status reflected in Dashboard System/Health Check
**Rationale**: Operator primary interface is Dashboard, not third-party tools
**Status**: PENDING

---

## New Archive Structure

Create these directories:

```
artifacts/
├── deprecated-notebooks/
│   ├── README.md
│   └── [archived .ipynb files]
├── deprecated-reports/
│   ├── README.md
│   └── [archived HTML/Jekyll outputs]
├── deprecated-pdfs/
│   ├── README.md
│   └── [archived COMET LEAP PDFs]
└── deprecated-dashboards/
    ├── README.md
    └── [archived legacy dashboard code]
```

Each README explains:
- Why surface was archived
- How functionality moved to primary Dashboard
- Where to find equivalent in Dashboard
- Date archived and operator approval reference

---

## Held Items (Dashboard)

These 6 items are explicitly blocked on operator approval. Do NOT attempt to advance without operator decision in Dashboard:

1. **Dual-boot NixOS install**
   - Blocker: Physical hardware access needed
   - Approval path: Operator confirms on-site capability

2. **Live fleet runtime proof**
   - Blocker: Cash cleared + safety gates confirmed
   - Current: 18% readiness
   - Approval path: Operator confirms demo readiness gate

3. **Style convergence batch auto-run**
   - Blocker: Disabled in batch mode to avoid unreviewed markdown rewrites
   - Approval path: Operator requests manual run per-file, then approves batch mode

4. **AWS CLI MCP / Bedrock MCP**
   - Blocker: Held in MCP canary registry (enabled=false)
   - Approval path: Operator enables when AWS credential store ready

5. **GitHub API (authenticated)**
   - Blocker: Requires auth token set + operator approval
   - Approval path: Operator provides token, approves scopes

6. **Netlify deploy**
   - Blocker: netlify.toml created, not yet deployed
   - Approval path: Operator confirms DNS routing, approves production deployment

---

## Implementation Checklist

- [ ] Create `artifacts/deprecated-notebooks/` with README
- [ ] Create `artifacts/deprecated-reports/` with README
- [ ] Create `artifacts/deprecated-pdfs/` with README
- [ ] Create `artifacts/deprecated-dashboards/` with README
- [ ] Move/archive all notebook files
- [ ] Move/archive all report outputs
- [ ] Move/archive COMET LEAP PDFs (9 files)
- [ ] Update removed surface README files with deprecation notices
- [ ] Verify Dashboard covers all migrated functionality
- [ ] Deploy Dashboard to production Netlify (pending operator approval)
- [ ] Remove legacy surface code from active implementation
- [ ] Commit consolidation to master branch

---

## Approval Gate

**Dashboard is now the ONLY operational surface for Lantern OS v1.0.0.**

All operator decisions flow through Dashboard.
All agent execution tracked in Dashboard Evidence.
All deployment status visible in Dashboard System.
All blockers explicit in Dashboard Held section.

No parallel surfaces carry authority. No external tools override Dashboard decisions.

---

**Consolidation Approved By**: Alex Place (Operator)
**Effective Date**: 2026-05-31
**Status**: ACTIVE IMPLEMENTATION
