# Portfolio Evidence Landing Page

Status: active portfolio path  
Audience: hiring managers, staff engineers, CTO reviewers, and technical interviewers  
Scope: evidence-backed overview of `gm-agent-orchestrator`

---

## 90-second summary

`gm-agent-orchestrator` is a Windows-first local AI work orchestration control plane. It coordinates coding/research agents through GitHub issues and PRs, local worktrees, task queues, MCP-style tool boundaries, provider preflight checks, dashboard/status snapshots, and deterministic validation.

The project is strongest as an operator/control-plane prototype. This portfolio path exists to answer the hiring-manager questions directly:

- Did it actually run?
- How often did it run?
- What failed?
- What got safer or more reliable after the failure?
- Which contract claims are enforced by scripts/tests versus still aspirational?

---

## Why this matters

Agentic IDEs help one developer complete one task inside an editor session. This repo explores the next layer: how an operator supervises multiple agents, local tools, provider limits, queue state, evidence, and recovery without blindly trusting model output.

The portfolio claim is not "production SaaS." The claim is:

> A local-first AI operations prototype with production-style controls, explicit safety contracts, and growing evidence coverage.

---

## Architecture at a glance

```text
Human/operator
  -> GitHub issues / PRs / task docs
  -> local orchestrator scripts
  -> task queue: queue -> active -> done/failed
  -> isolated worktrees per agent slot
  -> MCP-style local tool boundary
  -> provider preflights and capacity state
  -> dashboard/status snapshots
  -> contract tests and CI gates
```

Core design choices:

- use files, PRs, and logs as durable state;
- prefer read-only inspection before mutation;
- keep local MCP/tool state authoritative over remote assumptions;
- treat provider limits and preflight failures as first-class dispatch blockers;
- require validation evidence before claiming completion.

---

## Current evidence pack

| Evidence | Purpose | Status |
|---|---|---|
| [`evidence/demo-run-001.md`](evidence/demo-run-001.md) | Capture a redacted dry-run transcript showing startup/status/test paths. | Template ready; needs fresh local run transcript. |
| [`evidence/dashboard-snapshot-001.md`](evidence/dashboard-snapshot-001.md) | Capture dashboard/status screenshot or JSON snapshot. | Template ready; needs fresh redacted screenshot/snapshot. |
| [`evidence/queue-transition-001.md`](evidence/queue-transition-001.md) | Show a safe queue transition with before/after state. | Template ready; must be captured only from approved dry-run or redacted run. |
| [`evidence/test-output-001.md`](evidence/test-output-001.md) | Record CI/local test command output. | Initial CI surface documented; needs latest run output pasted. |
| [`evidence/failure-recovery-001.md`](evidence/failure-recovery-001.md) | Show one real failure and the reliability improvement. | Seeded with Gemini MCP preflight blocker example; needs attached logs/test output. |
| [`evidence/pr-review-examples.md`](evidence/pr-review-examples.md) | Point reviewers at representative PRs and what they prove. | Seeded with initial examples; keep current. |

---

## Contract-to-code traceability

Start with [`contract-enforcement-matrix.md`](contract-enforcement-matrix.md) to see which claims are:

- enforced by scripts/tests;
- partially enforced;
- CI-listed but needing spot-check evidence;
- documentation-only and not yet production claims.

This is intentionally conservative. If a contract claim is not backed by code/test/evidence, it should be marked as a gap instead of implied.

---

## Best reviewer path

1. Read this page.
2. Skim the root [`README.md`](../../README.md) for repo context.
3. Open [`contract-enforcement-matrix.md`](contract-enforcement-matrix.md).
4. Review [`evidence/failure-recovery-001.md`](evidence/failure-recovery-001.md).
5. Review [`evidence/test-output-001.md`](evidence/test-output-001.md).
6. Inspect the linked PR examples.

---

## What this project does not yet prove

This evidence path must stay honest. The repo should not claim production-grade readiness until there is repeated evidence for:

- queue locking/idempotency under concurrent workers;
- complete MCP authentication/authorization story;
- repeated successful dispatch cycles across multiple agents;
- long-running dashboard/service uptime;
- secret-safe logs and redaction policy;
- reliable cross-machine bootstrap from a clean environment;
- measured recovery time from common failure modes.

---

## Next evidence milestones

1. Capture a local dry-run transcript that does not start agents or move tasks.
2. Capture a dashboard/status snapshot with private paths and secrets redacted.
3. Capture one queue transition example with before/after state.
4. Attach latest CI output from Orchestrator Health.
5. Add a measured reliability snapshot after at least three repeated demo runs.
