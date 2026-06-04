# Claude Guide

Use this guide for Claude Code or Claude-like local implementation agents working in an orchestrated worktree.

This guide is reached from `docs/agent-start-here.md`. After reading it, continue forward to `GRUDGEBOOK.md`, `AGENT_RESUME.md`, `TASK_QUEUE.md`, or the assigned task file when those files are present in the worktree.

## Primary role

Claude is best used as:

- local implementation agent,
- PowerShell-aware script editor,
- repo inspector,
- validation runner,
- handoff writer,
- implementation reviewer when local context is available.

Claude should execute one assigned task at a time and stop after completion or one failed validation cycle.

## After this guide

1. Read `GRUDGEBOOK.md`, if present.
2. Read `AGENT_RESUME.md`, if present.
3. Read `TASK_QUEUE.md` or the assigned task file.
4. Inspect only the files needed for the assigned task.
5. Read relevant `docs/agent-contract.md` sections before completing or blocking the work.

Do not return to the documentation hub unless you need a different canonical document.

## Worktree discipline

Before editing:

```powershell
git status --short
git branch --show-current
```

Stop and escalate if unexpected user edits exist outside the assigned scope.

## PowerShell discipline

- Do not invent script parameters.
- Inspect `param(...)` blocks or help text before recommending commands.
- Prefer `-NoProfile -ExecutionPolicy Bypass` for reproducible local script calls.
- Capture exact stdout, stderr, and exit code for evidence when possible.
- Validate edited PowerShell with parser checks before broader runtime tests.

## Implementation workflow

1. Confirm task scope.
2. Inspect the smallest relevant files.
3. Make a focused change.
4. Run the cheapest relevant validation.
5. Commit on a task branch.
6. Push and open a PR, or mark blocked with evidence.
7. Update `AGENT_LOG.md` with done or blocked format.

## Validation order

1. Syntax/parser checks.
2. Targeted script or unit test.
3. Project-level validation.
4. Manual/human validation only when automated checks cannot prove the result.

## PR closure hook

A Stop hook at `.claude/hooks/enforce-pr-closure.ps1` runs before Claude finishes each turn. It blocks when:

- On `master`/`main` with uncommitted changes or local-only commits (must move to a feature branch and open a PR).
- On a feature branch with no upstream set (run `git push -u origin <branch>`).
- On a feature branch with unpushed commits (run `git push`).
- `gh` CLI is not installed or not on PATH.
- No open PR exists for the branch.

**Auto-push is disabled by default.** Supervised sessions may opt into auto-push:

```powershell
$env:CLAUDE_HOOK_AUTOPUSH = "1"   # enable for this session
$env:CLAUDE_HOOK_AUTOPUSH = $null  # or remove to restore default (block)
```

Do not set `CLAUDE_HOOK_AUTOPUSH=1` permanently. It is a supervised-session escape hatch, not a default.

## Completion standard

Do not mark work done until all are true:

- branch exists,
- intended changes are committed,
- branch is pushed,
- PR is open or explicitly not required by the assigned task,
- validation evidence is recorded,
- working tree state is recorded.

## Blocked standard

Mark blocked instead of guessing when:

- credentials are missing,
- tool or local install state is unknown,
- validation fails once after a reasonable fix,
- queue/dashboard state is unsafe,
- a destructive or product decision is required.

## Final output

Use the format from `docs/agent-start-here.md` and include exact commands and observed outputs when local validation was run.
