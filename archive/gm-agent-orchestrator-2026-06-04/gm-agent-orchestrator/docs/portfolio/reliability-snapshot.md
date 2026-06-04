# Reliability Snapshot

Status: metric definitions and initial evidence plan  
Purpose: answer "How reliable is it, and what improved?"

---

## Current stance

Do not invent reliability numbers. Until repeated runs are captured, treat this page as a metric definition and evidence checklist.

The portfolio should separate:

- measured data;
- sample/dry-run data;
- CI-listed checks;
- intended future metrics.

---

## Metrics to track

| Metric | Definition | Current value | Evidence source | Status |
|---|---|---:|---|---|
| Demo runs attempted | Number of captured read-only portfolio demo runs. | 0 | `evidence/demo-run-*.md` | Not yet measured |
| Demo runs succeeded | Number of captured demo runs that completed defined checks. | 0 | `evidence/demo-run-*.md` | Not yet measured |
| Queue transitions captured | Number of redacted safe queue transitions documented. | 0 | `evidence/queue-transition-*.md` | Not yet measured |
| Failure/recovery examples | Number of real failure modes with before/after evidence. | 1 | `evidence/failure-recovery-001.md` | Partial |
| Contract checks listed in CI | Named checks in Orchestrator Health workflow. | See workflow | `.github/workflows/orchestrator-health.yml` | CI-listed |
| Latest CI pass rate | Latest Orchestrator Health result. | TODO | GitHub Actions run | Evidence needed |
| Provider preflight blocks | Count of dispatches blocked by provider/MCP preflight. | TODO | status files/logs | Evidence needed |
| Recovery time from known failure | Time from failure discovery to merged/tested hardening. | TODO | PR + issue timestamps | Evidence needed |

---

## Reliability narrative so far

The strongest current reliability story is failure-driven hardening around Gemini dispatch:

```text
Problem: auth/preflight could pass while MCP was unhealthy.
Change: add MCP-aware preflight detection and dispatch blocker.
Evidence: PR #295, Gemini preflight/dispatch contract tests, CI workflow entries.
Gap: paste redacted local test output and preflight JSON.
```

---

## Evidence needed before stronger claims

Before calling the system production-grade, capture:

1. Three repeated read-only demo runs on current master.
2. At least one redacted queue transition with before/after state.
3. At least one dashboard/status snapshot.
4. Latest CI output for all Orchestrator Health jobs.
5. One blocked unsafe action transcript.
6. One provider quota/preflight blocked dispatch transcript.

---

## Current claim level

Credible claim:

> Portfolio-grade local AI orchestration prototype with explicit contracts, CI-listed checks, and initial failure-driven hardening evidence.

Do not yet claim:

> Production-grade multi-agent orchestration platform.
