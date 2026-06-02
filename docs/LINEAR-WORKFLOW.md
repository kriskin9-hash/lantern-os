# Linear Workflow for Lantern OS Repo Reset

**Status:** Phase A Setup  
**Date:** 2026-06-01  
**Audience:** Operators (2-3 trained team members)  
**Owner:** Founder

---

## Quick Overview

Linear is the **single source of truth** for Lantern OS cleanup work.

- **Backlog:** All work items live here
- **Cycles:** 4-week sprints (Cycle 1: Jun 1-14, etc.)
- **Issues:** Each cleanup task is an issue
- **Status:** Backlog → In Progress → Ready for Review → Done

GitHub issues #46-52 are linked for context but Linear is authoritative.

---

## Getting Started

### 1. Access Linear

- **Workspace:** Lantern OS
- **Team:** Repo Reset
- **URL:** `https://linear.app/lantern-os`

### 2. Claim an Issue

**How to claim:**
1. Go to the Backlog (default view)
2. Click an unassigned issue (no Assignee)
3. Click the Assignee field
4. Select your name
5. Click "In Progress" to start work

**Only claim what you can complete this week.**

### 3. Update Status as You Work

| Status | Meaning | When to use |
|--------|---------|------------|
| **In Progress** | You're actively working on it | Just started or working now |
| **Ready for Review** | Done, waiting for Founder review | Code complete, ready to commit |
| **Done** | Merged to master, closed | PR approved and merged |

**To update status:** Click the Status dropdown on the right side of the issue.

### 4. Comment with Progress

Add comments as you work:
- "Started Phase 1 mytholo gy doc deletion"
- "Deleted 45 files, 15 remaining"
- "Ready for review, PR linked below"

**Pro tip:** Paste the PR URL in a comment for easy traceability.

---

## Issue Structure

Each issue has this format:

```
Title: [Phase #] — [Action]

Description:
- What needs to be done
- Acceptance criteria (how to know it's done)
- Related files/directories

Example:
Title: Phase 1 — Delete HFF mythology docs
Description:
- Delete ~85 docs in HFF/docs/ matching mythology pattern (TARDIS, spine, anchor, etc.)
- Verify grep -ri "TARDIS\|spine\|anchor" returns 0 matches in docs/
- Update GitHub issue #47 with status after deletion
```

---

## Weekly Workflow

### Monday–Thursday: Work on Issues
1. Claim an issue from Backlog
2. Do the work (locally on your PC)
3. Update status to "Ready for Review"
4. Comment with PR URL or implementation notes
5. Await Founder review

### Friday: Status Sync

**Weekly Friday check-in (10 min):**
- Founder reviews all "Ready for Review" issues
- Approves merge or requests changes
- Celebrates completed work
- Re-prioritizes if needed

**No sync call required** — all async via Linear comments.

---

## Workflow for Phase 1 (Cleanup)

### Issues in Cycle 1 (Jun 1-14)

| Issue # | Title | Owner | Status |
|---------|-------|-------|--------|
| L-1 | Phase 0 — Fix top-level files | TBD | Backlog |
| L-2 | Phase 1 — Delete HFF mythology docs | TBD | Backlog |
| L-3 | Phase 1 — Delete gm-agent-orchestrator/lantern/ | TBD | Backlog |
| L-4 | Phase 2 — Strip HFF overengineering | TBD | Backlog |
| L-5 | Phase 3 — Validate Tier 3 docs | TBD | Backlog |
| L-6 | Phase 4 — Update READMEs + docs | TBD | Backlog |

### How Each Phase Flows

```
Backlog
  ↓
Claim issue (assign to yourself)
  ↓
Local work (branch: cleanup/phase-X-*)
  ↓
Push to GitHub, open PR
  ↓
Update issue: Status → Ready for Review
Comment: "PR: https://github.com/alex-place/lantern-os/pull/XXX"
  ↓
Friday: Founder reviews PR
  ↓
Approve → Merge → Update issue: Status → Done
  ↓
Complete! Move to next issue
```

---

## Communication Norms

### Async First

Post updates in Linear comments, don't wait for real-time discussion.

**Good comment:**
> Started Phase 1 deletion today. Removing ~85 HFF mythology docs (TARDIS, spine, anchor patterns). I'll grep the docs/ folder tomorrow to verify all removed. Expected completion: Wed afternoon.

**Avoid:**
> "Hey, need to talk about Phase 1" (without context)

### Blockers

If stuck, comment in the issue with:
- What you're trying to do
- What's blocking you
- What you need from the Founder

**Example:**
> Blocked: HFF/docs/TARDIS-anchor.md has 2,000 lines and references appear in 3 other files. Should I:
> A) Delete all references recursively
> B) Keep anchor references, delete only TARDIS files
> C) Create a DEPRECATION note instead
>
> Please advise by EOD so I can continue.

Founder will reply within 24h.

### PR Comments

Link the PR in Linear:

> PR ready for review: https://github.com/alex-place/lantern-os/pull/123
> 
> Changes:
> - Deleted 85 mythology docs in HFF/docs/
> - Updated CONTRIBUTING.md to point to Linear
> - grep verification: TARDIS|spine|anchor = 0 matches
> - All tests passing
>
> Ready to merge

---

## Acceptance Criteria Checklist

Each issue has an "Acceptance" section. Before marking Done:

- [ ] All changes made (compare against issue description)
- [ ] Tests pass (if applicable)
- [ ] grep verification passes (if cleanup)
- [ ] PR approved by Founder
- [ ] PR merged to master
- [ ] Code comment updated (if needed)

---

## Branch Naming Convention

All cleanup work goes to branches named:

```
cleanup/phase-[N]-[description]
```

Examples:
- `cleanup/phase-0-fix-top-level`
- `cleanup/phase-1-delete-mythology`
- `cleanup/phase-2-strip-overengineering`
- `cleanup/phase-4-update-readmes`

**Why:** Easy to search, groups related work, prevents conflicts.

---

## Merge Process

When your PR is approved:

1. **Merge to master** (not squash, not rebase — merge commit)
2. **Delete your branch** (GitHub will offer)
3. **Update Linear issue:** Status → Done
4. Comment in Linear: "Merged as commit abc123def"
5. **Claim next issue** if available

---

## Common Questions

### Q: Can I work on multiple issues at once?

**A:** Yes, but claim them first so others know you're on them. Prioritize finishing each phase before moving to the next.

### Q: What if I need more time?

**A:** Comment in the issue with an updated ETA. Founder will adjust priority if needed.

### Q: Can I change the acceptance criteria?

**A:** Ask in the issue comment before starting. Founder will clarify or adjust.

### Q: Do I need to sync with other operators?

**A:** Not required. Linear comments are your sync mechanism. Cycles are designed so phases don't overlap.

### Q: What if the Founder is unavailable Friday?

**A:** Async review continues. Founder will review PRs whenever available. No hard deadline, just next business day target.

---

## Glossary

| Term | Meaning |
|------|---------|
| **Backlog** | All unstarted work |
| **In Progress** | Currently being worked on |
| **Ready for Review** | Done, awaiting Founder approval |
| **Done** | Merged and closed |
| **Cycle** | 2-week sprint window (Jun 1-14, Jun 15-28, etc.) |
| **Issue** | Single cleanup task (e.g., "Delete mythology docs") |
| **Assignee** | The operator responsible for this issue |

---

## Support

If you have questions about Linear or the workflow:

1. Check this doc (you're reading it!)
2. Ask in the issue comment
3. Check previous issues for examples of how work was done

---

**Last Updated:** 2026-06-01  
**Next Review:** 2026-06-07 (end of Cycle 1)
