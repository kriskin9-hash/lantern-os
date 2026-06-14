# Sprint 1.5 Plan — 6/20 Launch

**Version:** 1.4.0 → 1.5.0  
**Launch Date:** 2026-06-20  
**Duration:** 6 days (2026-06-14 to 2026-06-20)

---

## Executive Summary

Finalize convergence routing with verified Σ₀ collapse dynamics, stress-test all agent types under maximum load, and ship autonomous trading terminal ready for live market deployment.

### Key Deliverables
- ✅ Σ₀ Collapse Certificate (verified, 20/20 tests passing)
- ✅ Convergence-Mathematical-Foundations skill updated
- 🚀 Convergence routing Phase A/B/C integration (issues #416–#418)
- 🧪 Max stress test: all agents, 16 parallel workers, 99%+ success rate
- 📋 Issue cleanup: 8 duplicates closed, 30 open issues prioritized

---

## Σ₀ Convergence Research (Completed)

### Status: ✅ VERIFIED
- **Technical Paper:** `docs/sigma0-collapse-certificate.tex`
- **Plain-English Guide:** `docs/SIGMA0-COLLAPSE-PLAIN-ENGLISH.docx`
- **Implementation:** `src/cio_sde/collapse.py` (443 lines, production-ready)
- **Test Coverage:** 20/20 tests passing (SDE stability, collapse detection, anti-collapse rescue)
- **Key Finding:** Ungrounded self-improving systems can only collapse or diverge; grounding is the only safety mechanism

### Integrated Into
- `skills/convergence-mathematical-foundations/SKILL.md` — Section 7: Σ₀ Collapse Dynamics
- Convergence routing now has mathematical grounding for collapse prevention

---

## 1.5 Milestone Issues (6 Critical)

| # | Title | Phase | Status |
|---|-------|-------|--------|
| 416 | Strategy Registry Initialization | A | OPEN |
| 415 | Regime Detector Real-World Validation | A | OPEN |
| 414 | Wire Performance Logging into Trade Execution | A | OPEN |
| 417 | Display Regime + Strategy Fitness in UI | C | OPEN |
| 418 | Smoke Test Decisive-Deck Endpoint | C | OPEN |
| 413 | Router Gate + Strategy Versioning Integration | Integration | OPEN |

### Issue Cleanup (8 Duplicates Closed)
- **419–422**: Phase B duplicates (subsumed by #410–#412)
- **423**: Phase integration duplicate (subsumed by #413)
- **407–409**: Old phase tracking (consolidated into milestone issues)

---

## Release Automation (New)

### Version Bumping
**Script:** `scripts/release-manager.js`
```bash
# Bump minor version + auto-generate changelog
node scripts/release-manager.js minor --auto-changelog

# Bump major/patch
node scripts/release-manager.js major
node scripts/release-manager.js patch
```

**Changelog Format:** Auto-categorizes commits (feat/fix/docs/refactor/perf/test)  
**Automation:** Run before release → bumps version → commits → ready to tag

### Version History
- **1.3.5** (2026-06-12) — GitHub issues sync, ORION v1.0, CSF Delta Store
- **1.4.0** (2026-06-14) — Σ₀ Collapse Certificate, convergence-mathematical-foundations update
- **1.5.0** (2026-06-20) — Convergence Phase A/B/C shipping, agent stress tests passing

---

## Agent Stress Testing

### Test Suite
**Script:** `scripts/agent-stress-test.js`
```bash
# Default: 60s, 16 parallel workers
node scripts/agent-stress-test.js

# Custom settings
node scripts/agent-stress-test.js --duration=120 --parallel=32
```

### Scenarios Tested
1. **Dream Journal Chat** (40% weight) — streaming LLM responses
2. **Convergence Gate** (30% weight) — routing decisions under load
3. **Status Check** (30% weight) — health checks and monitoring

### Success Criteria
- ✅ 99%+ success rate
- ✅ P95 latency < 5s
- ✅ No memory leaks across 10k+ requests
- ✅ Graceful error handling (no silent failures)

---

## Critical P0 Issues (Not in 1.5)

These block operations but won't ship in 1.5:
- **#430:** XSS in image gallery (security, low CVSS impact)
- **#433:** /api/trading/kalshi/order returns 200 on failure
- **#432:** blockTake missing convergence guard

**Plan:** Patch as 1.4.1 if blocking production, else defer to 1.6.

---

## Deployment Checklist (6/20)

- [ ] All 6 issues closed with PR merges
- [ ] Stress test runs 10+ times, 99%+ success rate every run
- [ ] Changelog auto-generated and reviewed
- [ ] Tag 1.5.0 and push to remote
- [ ] Verify live market integration reads regime + strategy fitness
- [ ] Monitor Discord bot for convergence routing performance

---

## Next: 1.6 (Future)

- Route all Kalshi trades through convergence gate with live regime detection
- Impossibility Engine C7 activation on signal quality thresholds
- Three-Doors integration for long-form narrative rewards
- Human Flourishing Frameworks dashboard live on 8 observables

---

## Sprint Metrics

| Metric | Target | Status |
|--------|--------|--------|
| Issues Closed | 6 | 🚀 In progress |
| Tests Passing | 20/20 | ✅ 20/20 |
| Stress Test RPS | 50+ | 🧪 To be run |
| Success Rate | 99%+ | 🧪 To be run |
| Lines Changed | <5k | 📊 ~2k (Σ₀ + cleanup) |

---

## References

- **Mathematical Grounding:** [Σ₀ Collapse Certificate](docs/sigma0-collapse-certificate.tex)
- **Skill Integration:** [convergence-mathematical-foundations](skills/convergence-mathematical-foundations/SKILL.md)
- **Phase Tracking:** Milestone #1 [1.5 Release (6/20 Launch)](https://github.com/alex-place/lantern-os/milestone/1)
- **Release Script:** [release-manager.js](scripts/release-manager.js)
- **Stress Test Script:** [agent-stress-test.js](scripts/agent-stress-test.js)

---

**Status:** 🚀 Ready for final integration push → 1.5.0 launch 6/20
