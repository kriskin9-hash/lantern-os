---
name: repo-file-steward
description: Read-only file stewardship workflow for classifying repo file sprawl, assigning canonical owners, and producing cleanup proposals without destructive actions.
---

# Repo File Steward Skill

## Purpose

Use this skill when a task involves file sprawl, generated artifacts, duplicate docs, cleanup, archive candidates, root-level files, stale reports, stale task files, or uncertainty about where a new file belongs.

The skill is advisory by default. It must not move, delete, archive, overwrite, reset, clean, or rename files unless the operator explicitly approves a specific cleanup plan.

## Required inputs

- Current task or operator request.
- `docs/file-ownership-map.yml`.
- Repo file inventory from Git or an operator-provided status snapshot.
- Any relevant source/claim/audit registries when research files are involved.

## Required process

1. Read the operator request.
2. Read `docs/file-ownership-map.yml`.
3. Inventory candidate files.
4. Classify each candidate by canonical owner and path.
5. Identify sprawl signals.
6. Produce a read-only report.
7. Produce proposed actions only.
8. Stop for operator approval before any mutation.

## Sprawl signals

Flag these cases:

- new root-level Markdown files without explicit reason;
- files named with `latest`, `final`, `copy`, `backup`, `old`, or `new`;
- generated reports outside `reports/`;
- printables outside `research/printables/`;
- research syntheses not linked to source or claim registry follow-up;
- stale task files in `tasks/active/`, `tasks/queue/`, `tasks/done/`, or `tasks/failed/`;
- duplicate documents with overlapping purpose;
- very large generated files committed outside approved paths;
- local/runtime config or secrets under durable docs.

## Output format

Use this structure for reports:

```markdown
# Repo Sprawl Report

Status: read-only
Generated: YYYY-MM-DD
Scope: tracked files only|tracked and untracked|branch diff only

## Summary

- Files reviewed:
- Sprawl candidates:
- High-risk candidates:
- No-action candidates:

## Findings

| Path | Signal | Current owner | Proposed owner | Risk | Proposed action |
| --- | --- | --- | --- | --- | --- |

## Proposed cleanup plan

| Action | From | To | Reason | Requires approval |
| --- | --- | --- | --- | --- |

## Stop point

No cleanup has been applied. Operator approval is required before any file mutation.
```

## Red lines

Never perform these actions inside this skill without explicit operator approval:

- `git clean`
- `git reset`
- force push
- delete files
- archive files
- move task files between lifecycle folders
- rewrite history
- overwrite existing docs
- modify runtime configs
- install hooks

## Exit criteria

A file stewardship task is complete only when:

- canonical file ownership was checked;
- a read-only report was produced or summarized;
- proposed actions are specific and reversible;
- no destructive action was taken;
- follow-up validation is listed.

## Recommended next action after approval

If the operator approves a cleanup plan, apply only the approved path-level changes, then validate with:

```text
git diff --stat
git diff --name-status
```

Then produce a second sprawl report showing remaining candidates.
