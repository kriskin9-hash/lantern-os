# Failure Recovery 001: Gemini MCP Preflight Blocker

Status: initial evidence note, needs attached logs/test transcript  
Purpose: answer "What failed, and what got better?"

---

## Failure summary

Gemini CLI preflight could pass authentication checks while the MCP connection or local tool surface was unhealthy. That created a risk of dispatching a Gemini slot into a broken MCP state and getting silent or confusing task failures.

---

## Reliability improvement

PR #295 added MCP-aware Gemini preflight handling and dispatch blocking. The PR summary states that it:

- detects MCP issues in Gemini preflight output;
- sets `mcpIssueDetected` and `mcpIssueEvidence` in preflight output;
- fixes child job exit-code capture;
- adds a dispatch gate that blocks Gemini slots when preflight is absent, stale, unreadable, or MCP-unhealthy;
- adds contract tests for preflight output schema and dispatch blocking.

---

## Evidence links

| Evidence | Link / path | Status |
|---|---|---|
| PR | `#295` | Merged |
| Merge commit | `fc542eecb8f2038535a7f1f30d4c0c2b8e7607ad` | Merged |
| CI tests added | `tests/Test-GeminiCliPreflightContract.ps1`, `tests/Test-GeminiDispatchPreflightGate.ps1` | Present in workflow surface |
| Workflow bucket | `.github/workflows/orchestrator-health.yml` | Present |
| Local run transcript | TODO | Needed |
| Redacted preflight JSON | TODO | Needed |

---

## Before behavior

```text
Auth could pass while MCP/tool health was still unsafe for dispatch.
```

---

## After behavior

```text
Gemini dispatch is blocked when preflight is missing, unreadable, stale, or detects MCP issues.
```

---

## Validation to attach

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tests\Test-GeminiCliPreflightContract.ps1 -Root .
powershell -NoProfile -ExecutionPolicy Bypass -File .\tests\Test-GeminiDispatchPreflightGate.ps1 -Root .
```

Paste output:

```text
TODO: paste redacted validation output
```

---

## What this proves

- a real failure mode was identified;
- dispatch safety was improved by blocking unsafe work instead of blindly proceeding;
- the improvement has named tests and CI workflow coverage.

---

## What this does not prove

- Gemini provider reliability under all quota/rate-limit states;
- complete MCP auth/authorization;
- cross-provider fallback reliability;
- long-running dispatch success metrics.

---

## Follow-up

Add a redacted `status/gemini-preflight.json` example showing `mcpIssueDetected=true` and the dispatch blocker output from a local run.
