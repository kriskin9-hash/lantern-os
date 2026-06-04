---
name: async-batch-convergence
description: Batch repository convergence work with merge checks, accessibility-first status, and clear handoff for blocked pull requests.
---

# Async Batch Convergence Skill

Use this skill when the operator asks to batch branches, merge pull requests, converge open issues, or flatten work toward `master` while validation loops are still running.

## Core Rule

Batch only work that is visibly safe, mergeable, and aligned with the active release gates.

If a pull request is stale, conflicted, blocked by checks, or not mergeable, leave it open and write a handoff note with the next concrete action.

## Batch Loop

1. Inspect open pull requests against `master`.
2. Check draft state, mergeability, head SHA, base SHA, changed files, and risk area.
3. Sort by risk:
   - docs, reports, manifests;
   - config-only changes;
   - cleanup changes;
   - scripts and service launchers;
   - sensitive release, credential, disk, or machine-state work.
4. Merge only open, ready, mergeable PRs whose changed files match the stated purpose.
5. After each merge, re-read remaining PRs because `master` changed.
6. Stop when the next item is not mergeable or needs operator review.

## Batch Lanes

### Green lane

A PR can enter the green lane only when all are true:

- target is `master` or the repo default branch;
- PR is open;
- PR is not destructive cleanup unless explicitly reviewed;
- `mergeable` is true;
- the change is small or already scoped;
- validation path is clear.

Green lane action:

- mark ready for review if it is draft;
- squash merge with a clear title;
- immediately re-check open PR state after the merge.

### Yellow lane

A PR is yellow when it is useful but not safe to merge now.

Common causes:

- merge conflicts;
- large feature surface;
- stale branch;
- overlapping config changes;
- missing validation evidence.

Yellow lane action:

- keep it open as draft;
- add or update a handoff comment;
- list the next smallest validation step.

### Red lane

A PR or branch is red when it could destroy or hide work.

Common causes:

- branch deletion requested without evidence;
- force-update requested;
- disk, bootloader, credential, or payment mutation;
- unreviewed generated artifact dump;
- dirty worktree risk.

Red lane action:

- do not perform the action;
- provide a clear handoff and safer alternative.

## Handoff Rules

For blocked work, keep the PR open and state the next step:

- rebase on current `master`;
- resolve conflicts;
- split a large branch;
- run targeted tests;
- update validation evidence.

Do not try to make a PR mergeable by moving refs without a separate explicit review step.

## Accessibility Handoff Standard

When the operator mentions disability, WCAG, or difficulty using the UI:

- keep summaries short and structured;
- avoid dense tables unless values are brief;
- include exact PR numbers and next action;
- avoid relying on color alone;
- say what was done, what is blocked, and why.

## Accessible Status Output

Use short headings and compact lists.

Required sections:

- Done
- Merged
- Held
- Next action
- Evidence

Use tables only for short labels and statuses.

## Required Evidence After a Batch

Report:

- merged PR numbers and commit SHAs;
- PRs left open and reason;
- blockers that need rebase or conflict resolution;
- next safe command or UI action for the operator;
- whether release gates remain held.

## Arc Reactor Gate

Do not claim full readiness unless local controls, dashboard, MCP, AccessX, dual boot prep, cash status, release approval, and loop evidence are all green or explicitly held.

## Never

- Do not merge conflicted PRs.
- Do not force branch updates.
- Do not merge large service/runtime changes without validation evidence.
- Do not delete branches or rewrite refs as an accessibility accommodation.
- Do not claim release readiness without explicit approval.
