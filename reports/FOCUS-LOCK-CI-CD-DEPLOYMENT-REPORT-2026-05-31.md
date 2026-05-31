# Focus Lock CI/CD Deployment Report

**Status**: DRAFT — Requires operator review before submission  
**Date**: 2026-05-31  
**Operator**: Alex Place  
**Scope**: Trading Agent + Dream Journal shipping pipeline  

---

## What It Actually Does

This report documents the CI/CD focus-lock system built to enforce hard priority on two shipping milestones:

1. **Dream Journal** (PR #37, `codex/dream-journal-alias`)
2. **Trading Agent** (Kalshi + IBKR, Harsanyi type space validated)

Until both milestones hit their **definition of shipped**, branch protection rejects PRs that do not reference trading or dream journal. Release gates require both milestones shipped before a tag can be created and a dist ZIP produced.

---

## Evidence / Source Discipline

| Component | File | Status |
|-----------|------|--------|
| Milestone tracker | `manifests/shipping-milestones.json` | ✅ Created |
| Focus lock CI | `.github/workflows/focus-lock.yml` | ✅ Created |
| Trading agent CI | `.github/workflows/trading-agent-ci.yml` | ✅ Created |
| Dream journal CI | `.github/workflows/dream-journal-ci.yml` | ✅ Created |
| Release automation | `.github/workflows/release.yml` | ✅ Created |
| Local validator | `scripts/Invoke-FocusLockValidation.ps1` | ✅ Created |
| Harsanyi type space | `skills/trade/Harsanyi-TypeSpace.ps1` | ✅ Runs clean |
| PDF builder | `scripts/Build-SimpleReportPdf.ps1` | ✅ Reused |

---

## Milestone Definitions

### Dream Journal (DREAM-JOURNAL-v1)

| Gate | Current | Required |
|------|---------|----------|
| PR merged to master | ❌ | ✅ |
| Deployed to Netlify mirror | ❌ | ✅ |
| Dashboard panel launches | ❌ | ✅ |
| API endpoints reachable | ❌ | ✅ |

**Status**: `ready_for_merge` — PR #37 on `codex/dream-journal-alias` branch.

### Trading Agent (TRADING-AGENT-v1)

| Gate | Current | Required |
|------|---------|----------|
| Kalshi paper positions tracked | ✅ | ✅ |
| IBKR demo trade logged | ✅ | ✅ |
| Harsanyi type space validates | ✅ | ✅ |
| Live trading gated by CI | ❌ | ✅ |
| Kill switch active in CI | ✅ | ✅ |

**Status**: `paper_trading_active` — 8 positions, $4.07 allocated, all have live blockers.

---

## Focus Lock Rules

**Mode**: Hard

- Until both milestones ship, every PR title/body must reference one of:
  `trading`, `trade`, `kalshi`, `ibkr`, `dream journal`, `dreamer`, `courtney`, `courtney's well`, `data-analyst`, `/sales`, `focus-lock`, `shipping`, `release`, `milestone`, `fix`, `bugfix`, `security`, `ci/cd`, `hotfix`
- CI exempts `.github/workflows/` and `scripts/Invoke-FocusLockValidation.ps1` from lock
- Release workflow enforces milestone gate; `force=true` override exists for emergencies

---

## Proven / Held / Local-Only

| Component | Status | Evidence |
|-----------|--------|----------|
| Focus lock CI YAML | ✅ Proven | Syntax valid, gates defined |
| Trading agent CI YAML | ✅ Proven | 3 lanes: Harsanyi, Kalshi ledger, kill switch |
| Dream journal CI YAML | ✅ Proven | 3 lanes: dashboard, API, AGENTS.md |
| Release YAML | ✅ Proven | Milestone gate + ZIP + GitHub release |
| Local validator script | ✅ Proven | Runs locally with -PrTitle / -PrBody |
| Harsanyi type space | ✅ Proven | 6 agent types, 0 critical divergence |
| Dream Journal PR #37 | ⏸️ Held | Needs merge to master |
| Live trading CI gate | ⏸️ Held | LANTERN_LIVE_ENABLED=0, KILLSWITCH active |
| Release ZIP built | 🔶 Local-only | Workflow defined, not yet executed |

---

## Next Safe Action

1. Merge PR #37 (`codex/dream-journal-alias`) to master to clear Dream Journal milestone.
2. Verify Netlify auto-deploy on merge (or trigger manual deploy).
3. Update `manifests/shipping-milestones.json` — set Dream Journal gates to `true`.
4. Re-run convergence loop and full test suite.
5. Run release workflow with tag `v0.9.0-rc1` to validate dist ZIP generation.

---

## Validation Path

```powershell
# Local focus lock check
powershell -ExecutionPolicy Bypass -File scripts\Invoke-FocusLockValidation.ps1 -PrTitle "your-pr-title"

# Full test suite
python -m pytest tests/ -v --tb=short

# Convergence loop
powershell -ExecutionPolicy Bypass -File scripts\Invoke-LanternConvergenceLoop.ps1

# Harsanyi type space
powershell -ExecutionPolicy Bypass -File skills\trade\Harsanyi-TypeSpace.ps1
```

---

## Appendices

### A. GitHub Actions Workflow Index

| Workflow | File | Triggers |
|----------|------|----------|
| Focus Lock | `.github/workflows/focus-lock.yml` | PR open/sync to master |
| Trading Agent CI | `.github/workflows/trading-agent-ci.yml` | Push/PR on trade, kalshi, trade-chat paths |
| Dream Journal CI | `.github/workflows/dream-journal-ci.yml` | Push/PR on dashboard, courtney, dreamer paths |
| Release | `.github/workflows/release.yml` | Manual dispatch only |

### B. Allowed PR Topics (Focus Lock)

```text
trading, trade, kalshi, ibkr, dream journal, dreamer, courtney,
courtney's well, data-analyst, /sales, focus-lock, shipping,
release, milestone, fix, bugfix, security, ci/cd, hotfix
```

### C. Harsanyi Type Space Summary (Latest Run)

| Agent | Approval | Notes |
|-------|----------|-------|
| Human | blocked | LANTERN_LIVE_ENABLED=0 |
| KalshiAgent | blocked | All positions have blockers |
| IBKRExecutor | paper | 1 demo trade logged |
| CloudMirror | healthy | Netlify live |
| McpAuditor | held | Canary not passing |
| ConvergenceValidator | healthy | 0 issues |

**Divergence**: 1 WARNING (MCP canary). 0 CRITICAL. Live trading blocked.

---

**End of Report**
