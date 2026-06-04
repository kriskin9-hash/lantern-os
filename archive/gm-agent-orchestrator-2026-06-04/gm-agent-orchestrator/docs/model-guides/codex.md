# Codex Guide

Use this guide for Codex or Codex-like agents reviewing diffs, producing focused code changes, or responding to PR feedback.

This guide is reached from `docs/agent-start-here.md`. After reading it, continue forward to the relevant issue, PR, diff, task file, tests, or source files.

## Primary role

Codex is best used as:

- focused code implementer,
- PR reviewer,
- regression-test author,
- patch correctness checker,
- small refactor agent,
- validation-feedback loop participant.

Codex should prefer narrow, testable changes over broad repo rewrites.

## After this guide

1. Read the original issue, PR, task, or review request.
2. Read existing tests and scripts near the changed files.
3. Inspect only the code needed to evaluate or patch the concern.
4. Read relevant `docs/agent-contract.md` sections before claiming completion.

Do not return to the documentation hub unless you need a different canonical document.

## Review discipline

When reviewing:

- Anchor feedback to the changed lines.
- Separate correctness bugs from style preferences.
- Prefer one actionable fix per comment.
- State what failure mode the comment prevents.
- Do not request broad rewrites unless the diff creates a real maintenance or correctness risk.

## Implementation discipline

When changing code:

1. Keep the patch minimal.
2. Preserve public script parameters unless the task requires a breaking change.
3. Add or update targeted validation when behavior changes.
4. Test the production codepath, not a reimplemented copy of the behavior.
5. Avoid placeholder-only implementations.
6. Do not mix docs, refactors, and behavior changes unless the task requires it.

## Test discipline

A useful regression test should fail if the production behavior regresses.

Avoid tests that:

- duplicate the desired logic inside the test,
- assert only simulated helper behavior unrelated to production code,
- pass without exercising the changed file,
- rely on local-only paths without clear guards.

Prefer tests that:

- call the edited function/script directly,
- use fixtures for inputs and outputs,
- check exit codes and structured output,
- fail with a clear message.

## PR feedback loop

When addressing feedback:

1. Read the original issue and PR body.
2. Read every unresolved review thread.
3. Patch only the reviewed concern.
4. Add validation proving the concern is addressed.
5. Reply with the commit SHA and evidence.

## Final report

Include:

```text
Result: pass/fail/partial
Issue: #<number or none>
Branch: <branch or none>
Command: <exact command or not run>
Files changed: <short list or none>
Validation: <commands/checks run, or not run with reason>
Verified: <observable facts proven by evidence>
Assumed: <assumptions or none>
Grudgebook entry required: yes/no + reason
Review concerns addressed: <summary or none>
Remaining risks: <risks or none>
Next: <one action>
```
