# Lantern OS Single-Surface Consolidation

**Decision Date**: 2026-05-31
**Operator Approved**: Yes
**Status**: ACTIVE IMPLEMENTATION

## Overview

Lantern OS converges to a single unified dashboard surface as the canonical control plane for all v1.0.0 operations. All other surfaces (notebooks, reports, separate web views, legacy dashboards) are removed from implementation and their functionality is consolidated into this one surface.

## Primary Surface

**URL**: https://lantern-os-cloud.netlify.app/

**Status**: Live, operational, no auto-execute
**Access**: Operator-gated human approval required
**Health**: ok

## Dashboard Structure

### Main Navigation Sections

1. **Dream Journal AI ↻ Convergence2**
   - Primary user intent interface
   - Real-time convergence feedback loop
   - Counterfactual suggestion engine

2. **System**
   - Batch Jobs
   - Health Check
   - Repositories
   - MCP source management
   - Configuration state

3. **Publish**
   - RAG / PDF Sync
   - Agent Fleet
   - Deployment readiness
   - Release artifacts

4. **Evidence**
   - Arc Reactor (execution runtime)
   - Run Receipts (validation proofs)
   - Convergence audit trail
   - Safety gate history

5. **Held**
   - Blocked items (6 current)
   - Operator approval requirements
   - Physical action dependencies
   - Human gate status

## Surfaces to Remove / Consolidate

The following surfaces are hereby removed from active implementation and their functionality migrated to the primary dashboard:

1. **Legacy Jupyter Notebooks**
   - All .ipynb files → archived to `artifacts/deprecated-notebooks/`
   - Functionality → integrated into Dashboard Evidence section

2. **Static HTML Reports** (previous Jekyll build)
   - `_site/` outputs → archived
   - Report generation → via Dashboard Publish section

3. **Separate Repo Status Pages**
   - GitHub Pages secondary views → consolidated into System section
   - Repo health monitoring → unified in Dashboard System/Health Check

4. **COMET LEAP Surface PDFs**
   - One-off PDF reports → catalogued in Dashboard Evidence/Run Receipts
   - No separate PDF generation workflow; all output through Dashboard

5. **Email-based Reports**
   - Asynchronous report delivery → operator pulls from Dashboard on-demand
   - No push reports; Dashboard is pull-based, operator-gated

6. **Local Development Dashboards**
   - Development mode views → Dashboard System/Batch Jobs (local execution context visible)
   - No separate dev/prod surface distinction

7. **Third-party Monitoring Tools** (Netlify UI, GitHub UI for checks)
   - Status reflected in Dashboard System/Health Check
   - Operator uses Dashboard as primary, not external tools

## Consolidation Rules

### Rule 1: Single Source of Truth
Dashboard is THE interface for all human decision-making on Lantern OS operations. No parallel surfaces carry authority.

### Rule 2: No Auto-Execute
All automation is disabled by default. Human approval gate is mandatory before any agent action.

### Rule 3: Evidence Is Linked, Not Exported
Run receipts, validation proofs, and convergence audit trails remain in Dashboard Evidence section. External export happens only on operator request.

### Rule 4: Configuration Is Read From Manifests
Dashboard displays configuration state from:
- `manifests/lantern-mcp-sources.json`
- `config/` directory
- `.github/workflows/` (via System/Health Check)

Dashboard does NOT store configuration. It reads and displays it.

### Rule 5: Held Items Are Explicit
The "Held" section displays:
- Dual-boot NixOS install (physical action needed)
- Live fleet runtime proof (18% readiness, safety gates pending)
- Style convergence batch auto-run (disabled in batch mode)
- AWS CLI MCP / Bedrock MCP (canary registry held)
- GitHub API authenticated (token + operator approval needed)
- Netlify deploy (ready but operator hasn't approved)

No held item can advance without explicit operator decision in this Dashboard.

## Netlify Deployment

Current status: `netlify.toml` created, not yet deployed.

**Next**: Operator confirms dashboard URL → production DNS points to live netlify deployment → dashboard becomes live operational surface.

## Implementation Timeline

**Phase 1 (Complete)**: Create Dashboard, document consolidation plan
**Phase 2**: Archive all removed surfaces to `artifacts/deprecated-*/`
**Phase 3**: Publish deprecation notices in removed surface README files
**Phase 4**: Verify all functionality accessible via primary Dashboard
**Phase 5**: Deploy Dashboard to production Netlify
**Phase 6**: Operator approval to remove legacy surface code from repo

## Rollback

If Dashboard becomes unavailable:
1. Operator manually checks `manifests/open-issues.md` and `docs/CONVERGENCE-LOOP.md`
2. Operator reviews `scripts/Invoke-LanternConvergenceLoop.ps1` for state
3. Archived surfaces in `artifacts/deprecated-*/` are read-only reference only

## Future Expansion

No new surfaces are created. All feature requests go through Dashboard UX iteration.

---

**Approved by**: Alex Place (Operator)
**Date**: 2026-05-31
**Authority**: CONVERGENCE-LOOP.md Rule — expansion only after leading blockers handled
