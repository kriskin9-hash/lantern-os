# Script Archive Index - Disaster Recovery 2026-04

This folder is for retired or one-off scripts preserved from cleanup and disaster-recovery work.

## Rules

- Active automation stays in `scripts/`.
- One-off recovery, migration, audit, and scratch scripts move here only when they are no longer part of the supported run path.
- Each archived script entry must explain whether it is preserved for provenance, replaced by a current script, or intentionally cut.
- Archived scripts must not be called by CI, task runners, or first-read docs.

## Entries

| Script | Status | Reason | Replacement or follow-up |
| --- | --- | --- | --- |
| `claude_fix.ps1` | Preserved for provenance | One-off Claude/disaster recovery repair script from the scrambled recovery period; not part of the supported run path. | None. Revive only by copying the useful idea into a fresh branch from current `master` with tests. |
| `Fix-Dashboard.ps1` | Preserved for provenance | One-off dashboard repair helper from disaster recovery; current dashboard work must route through supported dashboard scripts/tests. | None. Revive only by copying the useful idea into a fresh branch from current `master` with tests. |
| `Fix-PostMergeIssues-v2.ps1` | Preserved for provenance | One-off post-merge cleanup script from recovery; broad repair scripts should not live at repo root. | None. Revive only by copying the useful idea into a fresh branch from current `master` with tests. |
| `RUN_AUDIT_CLAUDE_CROSS_REPO_ACCESS.ps1` | Preserved for provenance | Root audit launcher from recovery; audit work should use supported scripts or a fresh issue-linked branch. | None. Revive only by copying the useful idea into a fresh branch from current `master` with tests. |
| `RUN_AUDIT_TASK_VISIBILITY.ps1` | Preserved for provenance | Root audit launcher from recovery; task visibility audits should use supported scripts or a fresh issue-linked branch. | None. Revive only by copying the useful idea into a fresh branch from current `master` with tests. |

## Revival rule

To revive an archived script, copy the useful idea into a current branch from `master`, add tests where practical, and update this index with the new active location.
