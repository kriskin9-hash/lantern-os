# AGENTS

> This file follows the [AGENTS.md open standard](https://agents.md) — a predictable,
> repo-root format for guiding AI coding agents.

Repo: `gm-agent-orchestrator`

This repo owns local multi-agent orchestration: task queues, agent slots, worktrees, dashboard status, cross-repo priority reporting, reliability tracking, and token/rate-limit recovery.

It does **not** own GameMaker gameplay implementation. Game work belongs in `ChildOfLevistus`. Room/object inspection and preview tooling belongs in `gamemaker-room-editor`.

## Read first

1. `docs/README.md`
2. `docs/agent-start-here.md`
3. Your model guide:
   - GPT / ChatGPT: `docs/model-guides/gpt.md`
   - Claude: `docs/model-guides/claude.md`
   - Codex: `docs/model-guides/codex.md`
4. `docs/agent-contract.md`
5. `tasks/queue/` or assigned task file
6. `status/orchestrator.json`, if present
7. `status/priority.json`, if present
8. Open issues before creating new work

Important issue lanes:

- #15: cross-repo priority/status reporting
- #18: reliability ledger and local performance monitor
- #24: dashboard/watcher reliability and next-action UX
- #29: Gemini/filler-agent preflight only
- #30: Grudgebook contract language
- #32: repo-level agent instruction audit
- #34: Gemini slot runner hardening before unattended use

## Current priority rule

Dashboard, queue, and priority reporting reliability come before new agent expansion.

Do not enable Gemini, Aider, or other filler agents for unattended broad work until the dashboard can clearly show status, blockers, and next actions.

## Anti-redundancy rule

Before creating a new issue, task, script, config file, dashboard panel, helper, or documentation file:

1. Search existing files for similar work.
2. Search open issues and recent PRs for overlap.
3. Prefer extending or repairing existing systems over creating parallel ones.
4. If new work is still needed, state what existing work was checked and why it was insufficient.

## Honesty and operating-condition check

Before making a confident recommendation or changing repo state, check:

```text
Operating condition check:
- Am I moving too fast or skipping verification?
- Am I missing repo context?
- Is this task high-risk for false confidence, duplicate work, broad scans, or bad routing?
- Should I search existing issues/docs before acting?
```

If the answer is yes, slow down and verify first.

Do not guess about current tool pricing, quota, authentication, install state, or local process state. Verify locally or mark unknown/blocked.

Separate verified facts from assumptions in final reports.

## Grudgebook and reliability events

A grudge is a formal reliability/accountability event, not casual feedback.

Record or route grudges through the reliability ledger work in #18 and the contract language in #30. Do not erase grudges; they can only be marked addressed with evidence and a corrective rule.

Useful event names:

- `confident_false_claim`
- `thinking_too_fast`
- `constrained_operating_condition`
- `skipped_existing_issue_check`
- `overconfident_under_uncertainty`
- `dashboard_down_unclear_next_step`
- `queue_contract_not_consistently_used`

## Document authority hierarchy

When docs conflict, this order wins:

1. `AGENTS.md` — root policy and routing (this file)
2. `docs/agent-start-here.md` — mandatory reading path
3. `docs/model-guides/<model>.md` — provider-specific behavior
4. Assigned task file — local scope and acceptance criteria
5. `docs/agent-contract.md` — evidence, validation, handoff (on demand; read only the relevant section)

Everything else — drift-prevention-contract, dispatch-determinism-map, grudgebook, token-aware-protocol — is reference material. Do not treat it as mandatory startup reading.

`skills/` contains reusable operator-authored skill docs. Reference them when a task explicitly names a skill, or when a skill matches your current problem class.

## Control-plane freeze rule

The following files affect governance or runtime behavior. Do not change more than one in a single PR without explicit operator approval. Any PR touching these files must state which validation level was run (see `docs/agent-contract.md`):

- `AGENTS.md`, `CLAUDE.md`
- `.claude/settings.local.json`, `.claude/settings.supervised-write.json`
- `docs/agent-contract.md`, `docs/repo-structure-contract.md`, `docs/file-ownership-map.yml`
- `scripts/Start-GmAgentOrchestrator.ps1`, `scripts/Start-AgentSlot.ps1`, `scripts/Start-OrchMcpServer.ps1`
- `scripts/Invoke-OrchestratorAgentAction.ps1`, `scripts/Invoke-OrchestratorTaskAction.ps1`
- `scripts/Claim-OrchestratorQueueTask.ps1`, `scripts/Move-OrchestratorTask.ps1`
- `.claude/hooks/*.ps1`

Rapid successive changes to these files without stable audit checkpoints between them is a governance risk. See the grudgebook for past violations.

## Work rules

- Work on a branch, not directly on `master`.
- Agents must not create commits using the operator's personal Git identity. Use an explicit bot/agent identity for commits, or stop and ask the operator to commit.
- Use issue-linked branches, for example `feature/32-root-agents`.
- Keep changes small.
- Prefer docs/plan, implementation, then validation commits.
- Preserve public script inputs unless a change is required.
- Run the cheapest relevant validation first.
- Stop after one completed task or one failed validation cycle.

## Pull request and branch closure rule

Each agent must finish or explicitly block its current branch before opening a new feature branch.

Before starting a new branch for the same agent:

1. Push the current branch.
2. Open a pull request if one does not already exist.
3. Resolve review comments, merge conflicts, and failing checks that are in scope for that branch.
4. Merge the pull request to `master`, or close it with a clear blocked/abandoned reason.
5. Delete or retire the feature branch after merge/closure when it is no longer needed.
6. Record the PR number, merge/closure result, and next branch name in the handoff.

Do not accumulate multiple open feature branches per agent for related work. If follow-up work is needed, merge or close the existing PR first, then open a new branch from fresh `master`.

Exception: a separate emergency branch may be opened only for an urgent production/dashboard recovery. The emergency branch must name the blocker, avoid unrelated work, and still close before normal feature work resumes.

## Dashboard and queue rule

If dashboard state is unclear or down, do not continue agent expansion. Update #24 and provide one concrete recovery action.

If a task only exists on a feature branch or PR, say that clearly before asking Alex to run local commands.

## Final report format

```text
Result: pass/fail/partial
Issue: #<number>
Branch: <branch>
Command: <exact command or not run>
Files changed: <short list>
Validation: <pass/fail/not run + reason>
Verified: <facts verified>
Assumed: <assumptions or none>
Grudgebook entry required: <yes/no + reason>
Next: <one action only>
```
