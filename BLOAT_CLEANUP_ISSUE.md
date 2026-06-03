# Bloat Cleanup Issue

**Date:** 2026-06-03  
**Author:** Keystone  
**Status:** In Progress

## Summary

The repository has accumulated significant bloat over time. This document tracks verifiable bloat that has been identified and removed.

## Criteria for Deletion

Files/folders were considered verifiable bloat if they met one or more of the following:
- Clearly temporary (`.tmp-*` folders)
- One-off handoff artifacts with no ongoing value
- Duplicate or superseded files
- Generated/cache files that should never have been committed

## Deletions Performed

### 2026-06-03
- Deleted `.tmp-agent-fleet/` (7 files)
- Deleted `.tmp-dollhouse-csf/` (3 files)

**Reason:** Temporary processing folders with no long-term value.

## Planned Next Deletions (Requires Review)

- Root-level handoff documents older than 30 days (`*HANDOFF*`, `*DEPLOYMENT-REPORT*`)
- Duplicate bot implementations (`bot.py` + `bot_v2.py`)
- Multiple Dockerfiles in `ops/` and `services/`
- Old versioned files (`*-v2*`, `*-v3*`)

## .gitignore Updates

Added aggressive anti-bloat patterns to prevent future sprawl:
- `.tmp-*/`
- `*HANDOFF*`
- Old version markers (`*-v2*`, `*-old*`, `*-backup*`)
- Worktree artifacts

## Notes

- This cleanup is being done conservatively
- Major deletions will be done in small batches with documentation
- Goal: Reduce repo size and cognitive load without losing important history

---
**Next Action:** Review and delete old root-level handoff documents (with comments in commit messages)