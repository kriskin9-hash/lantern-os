---
name: incremental-implementation
description: Use when implementing any code or config change — ensures each step is validated and committed before the next begins, preventing cascading failures.
---

# Skill: Incremental Implementation

Status: active
Scope: All code, config, and script changes made by agents in this repo.

## Purpose

This repo has a validation-first delivery standard. Changes that land in one large commit are
harder to review, harder to bisect, and more likely to break the orchestrator mid-run. This
skill describes the increment boundary, commit discipline, and validation gate for each step.

## Core rule

One logical change per commit. A logical change is the smallest unit that leaves the repo in a
working state. It is not "all the changes for the task."

Examples of correct increment boundaries:
- Add one new MCP tool handler, with tests.
- Rename a set of related files in a single atomic rename commit.
- Fix one encoding bug in one function.
- Add one new route to a script with a corresponding config update.

## Implementation sequence

For each increment:

1. Read the task scope and the smallest set of source files needed.
2. Make exactly one logical change.
3. Verify locally:
   - If PowerShell: run the affected script with safe test args.
   - If MCP: confirm `/health` still returns `{"status":"ok"}` after restart.
   - If docs: confirm Markdown renders cleanly and no broken links in the changed file.
4. Commit with a message that explains the why, not just the what.
5. Only then move to the next increment.

## Commit message format

```
<type>: <what changed and why>

Evidence: <one-line observation proving the change works>
```

Types: `fix`, `feat`, `docs`, `refactor`, `test`, `config`.

Example:
```
fix: add UTF8 encoding to Get-TaskTitle to prevent em dash MCP parse failure

Evidence: Get-OrchestratorStatus returns valid JSON for tasks with em dash titles.
```

## Stop conditions

Stop and surface to the operator (do not continue) if:
- A validation step fails and the fix is not obvious from the task scope.
- The change requires touching more than 3 files outside the task scope.
- The MCP server fails to restart cleanly after a change.
- A test that was passing before is now failing.

Do not "fix forward" without surfacing. Submit what passed validation, note what did not.

## Evidence standard

Per `docs/agent-contract.md`, every task completion requires:
- One or more observable facts proving the change works.
- No unsupported claims ("this should work" is not evidence).
- If UI verification is required, a screenshot or explicit browser confirmation.

## Reference docs

- `docs/agent-contract.md` — Full evidence and handoff standard
- `docs/control-plane-ci-policy.md` — CI enforcement rules
- `docs/git-enforcement-implementation.md` — Git hook and branch naming rules
- `docs/drift-prevention-contract.md` — Rules for preventing architectural drift
