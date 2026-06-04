# PR Review Examples

Status: initial reviewer map  
Purpose: help a hiring manager inspect representative changes without reading every PR.

---

## Representative PRs

| PR | What to inspect | What it demonstrates | Notes |
|---|---|---|---|
| `#295` | Gemini MCP-aware preflight gate and dispatch blocker | Failure-driven hardening: detects MCP issues, blocks unsafe Gemini dispatch, adds tests and CI wiring. | Strong reliability story; attach validation transcript in `failure-recovery-001.md`. |
| `#294` | Repo cleanup for portfolio signal | Repo hygiene and canonical path cleanup. | Shows awareness that portfolio signal matters. |
| `#292` | Claude permissions and PR closure governance | Agent permission narrowing and PR lifecycle enforcement. | Review for hook behavior and false-positive risk. |
| `#300` | Deterministic-first PR governance advisor | Review process hardening; deterministic/static checks before model-heavy review. | Open at time of this evidence page; do not claim merged until merged. |
| `#298` | General work orchestration outline | Product framing: active objectives, policies, validation, evidence. | Open at time of this evidence page; may overlap with portfolio positioning. |

---

## Review questions for hiring managers

When inspecting a PR, ask:

1. Was the problem clearly described?
2. Was the mutation scope limited?
3. Were tests or deterministic checks added?
4. Did the PR explain validation and rollback?
5. Did the change improve reliability, safety, or observability?
6. Is the claim backed by code/tests/evidence, or only by docs?

---

## Evidence to add later

For each representative PR, add:

- link to PR;
- before/after behavior;
- exact files changed;
- exact validation output;
- reviewer comments, if any;
- merge status;
- follow-up gaps.
