# Operator Role — Lantern OS Repo

**Status:** Active operator instructions  
**Effective:** 2026-06-01 (Phase A implementation)  
**Audience:** Trained operators working on repo cleanup, features, and maintenance

---

## Your Role

You are a trained operator responsible for:
1. **Claiming issues** from the Linear backlog (not GitHub)
2. **Completing work** on local `cleanup/*` or `feature/*` branches
3. **Submitting PRs** for Founder review
4. **Communicating progress** via Linear comments (async, not Slack)
5. **Respecting boundaries** around private state, secrets, and configuration

**You are NOT responsible for:**
- Architecture decisions (Founder owns these)
- Merging to master (Founder approves)
- Release management
- Deployment decisions

---

## Starting Work

### 1. Read the Operating Rules

- **Inspect before editing:** Understand what a file does before changing it
- **Keep changes small:** PRs should be reviewable in <30 minutes
- **Do NOT import dirty state:** Only work with tracked files (git-clean)
- **Do NOT mutate system config:** No touching boot, firmware, partitions, disks
- **Do NOT claim readiness:** Founder signs off on production-readiness
- **Delete cleanly:** When removing files, grep for references first
- **Retire deprecated surfaces:** Don't leave broken docs or scripts

### 2. Understand the Repo

Read in this order:
1. **README.md** — what Lantern + Suzie are
2. **CONTRIBUTING.md** — commit message style, branch naming
3. **docs/LINEAR-WORKFLOW.md** — how to claim and complete work
4. **docs/REPO-CONTRACT.md** — what belongs in this repo (see Phase C Phase 0)

### 3. Claim an Issue

Go to **Linear workspace: Lantern OS**

1. Find your task in the **Backlog**
2. Click **Assign to myself**
3. Move status to **In Progress**
4. Comment: "Starting work"

### 4. Work Locally

```bash
# Create a branch (cleanup or feature style)
git checkout -b cleanup/phase-1-delete-mythology
# or
git checkout -b feature/add-orchestrator-endpoint

# Make your changes
# Test locally
# Commit with clear message

# Push to remote
git push origin cleanup/phase-1-delete-mythology

# Open PR (use GitHub web or gh cli)
gh pr create --title "Phase 1 — Delete mythology docs" --body "..."
```

### 5. Mark Ready for Review

In Linear:
- Update status to **Ready for Review**
- Comment with PR link: `https://github.com/alex-place/lantern-os/pull/123`
- Add any implementation notes or gotchas

### 6. Wait for Founder Review

Founder reviews **every Friday**. No need to ping — they check Linear daily.

If approved: **Merge and mark Done**  
If changes needed: **Update PR and re-comment in Linear**

---

## Operating Norms

### Communication

- **Async first:** Post in Linear, don't wait for Slack/Discord
- **Be specific:** "Deleted 45 mythology docs, 15 remaining" vs "working on phase 1"
- **Link to work:** Paste the PR URL in your comment for traceability
- **Ask early:** If stuck, comment in the issue with what you need from Founder

### Code Quality

- **Test your changes:** Run `pytest` if tests exist
- **No dead code:** Don't leave broken scripts or docs
- **No secrets:** Never commit tokens, passwords, or API keys (use `.env` files)
- **Clean git history:** One commit per issue, clear message, no "oops" commits

### Respect Boundaries

- **No live state in repo:** Never commit conversation logs, journal files, or `.lantern/state/`
- **No private names:** Don't include personal names of team members in code/docs
- **No mythology language:** Don't use TARDIS, spine, convergence, anchor, etc. in code/docs
- **No overengineering claims:** Don't claim features are "production-ready" or "v2.0" until Founder approves

---

## Common Workflows

### Cleanup Phase (Repo Reset)

You're responsible for removing old code/docs and documenting what stays.

```bash
# Example Phase 1 cleanup: delete mythology docs

# 1. Find all files matching the pattern
find docs/ -name "*TARDIS*" -o -name "*spine*" -o -name "*anchor*"

# 2. Verify no code depends on them
grep -r "TARDIS\|spine\|anchor" src/ --include="*.py" --include="*.ps1"

# 3. Delete the files
git rm docs/TARDIS-*.md docs/spine-*.md docs/anchor-*.md

# 4. Commit
git commit -m "Phase 1 — Delete mythology docs (TARDIS, spine, anchor)"

# 5. Verify
grep -r "TARDIS\|spine\|anchor" docs/ --include="*.md"  # Should return 0 matches
```

### Feature Work

You're adding a new capability (e.g., new API endpoint, new Discord command).

```bash
# 1. Create feature branch
git checkout -b feature/add-orchestrator-status-endpoint

## Change Control — Linear Ticket Gate + Anti-Sprawl (MANDATORY)

**All code changes to master must reference a Linear backlog ticket. CI blocks PRs that sprawl beyond ticket scope.**

Enforced by `linear-ticket-gate.yml` with three gates:

### Gate 1 — Linear ticket required

1. Every PR title, body, or branch name must contain a Linear ticket ID (e.g., `LAN-123`).
2. Agents must create or claim a Linear ticket **before** writing code.
3. No speculative, untracked, or "cleanup" PRs without a ticket.
4. Fabricated ticket IDs will be caught in review.

### Gate 2 — Anti-sprawl (blocks agentic overproduction)

CI will **fail** the PR if it detects:
- **New top-level directories** not already in master (agents love creating new modules)
- **>25 new files** in a single PR (scope creep signal)
- **>3 new markdown files** outside of AGENTS.md/README.md (doc sprawl)
- **>2 new Dockerfiles/requirements files** (infra sprawl)

Operator can override by adding `sprawl-approved` to the PR body.

### Gate 3 — No new repos or submodules

Submodule additions are blocked. Everything lives in this one repo.

### Exempt changes (no ticket required)

- `ci/`, `ci-`, `dependabot/`, `hotfix/` branch prefixes
- `ci:`, `chore(ci):`, `hotfix:`, `revert:` PR title prefixes

### Why

Agentic-first development caused: new repos nobody asked for, dozens of generated files per PR, doc sprawl, infra duplication, and scope drift. This gate forces agents to stay within the ticket scope and prevents the repo from growing sideways.

---

## One Repo Policy

**Everything lives in `lantern-os`.** Do not create separate repos for trading, Discord bots, dashboards, or any other surface. New modules go into existing directories or get a subdirectory approved via a Linear ticket.

---

## Branching

Use `codex/` branch names for agent work unless the operator asks otherwise. Include the Linear ticket ID: `codex/LAN-123-description`

---

## Asking for Help

**Stuck on a phase?** Comment in Linear:

> Blocked on Phase 2: HFF/apps/ has 12 subfolders. Should I:
> A) Delete only files matching mythology pattern
> B) Deprecate entire apps/, move to archive/
> C) Refactor individual apps to clean code
>
> Please advise by EOD.

Founder will reply within 24 hours.

---

## Escalation

If something breaks or doesn't match your understanding:

1. **Comment in Linear issue** with exact error message
2. **Include context:** file path, line number, what you were doing
3. **Provide evidence:** paste error output, test failure logs, etc.
4. **Don't guess:** ask Founder before proceeding if you're unsure

---

## Weekly Rhythm

| Day | Task |
|-----|------|
| Mon–Thu | Claim and work on issues |
| Fri | Founder reviews all "Ready for Review" PRs (async) |
| Fri | Celebrate completed work |
| Fri | Next Cycle backlog planned |

**No sync call required** — all async via Linear comments and PR reviews.

---

## Quick Reference

| Task | Command |
|------|---------|
| Clone repo | `git clone https://github.com/alex-place/lantern-os.git` |
| Create branch | `git checkout -b cleanup/phase-X-description` |
| Check changes | `git status`, `git diff` |
| Commit | `git commit -m "Phase X — [description]"` |
| Push | `git push origin cleanup/phase-X-description` |
| Open PR | `gh pr create --title "..." --body "..."` |
| Update Linear | Move issue status, add comment with PR URL |

---

## What Success Looks Like

✅ **A good week:**
- Claimed 1-2 issues from Linear
- Completed them locally with small, reviewable commits
- Opened PRs with clear descriptions
- Marked issues "Ready for Review"
- Responded to feedback from Founder
- Merged at least one PR

✅ **A good PR:**
- Solves one issue completely (not half)
- Has clear commit message
- All tests pass (if applicable)
- No dead code or broken docs
- No secrets or private data
- Linked in Linear issue

❌ **Red flags:**
- "Added X, still need to fix Y" (incomplete)
- Commits with messages like "WIP" or "oops" (unclear)
- No Linear comment linking the PR
- Code that seems to work but tests fail
- Old mythology language still in docs

---

**Last Updated:** 2026-06-01  
**Next Review:** 2026-06-14 (end of Phase C Phase 1)

**Questions?** Read `docs/LINEAR-WORKFLOW.md` or comment in your Linear issue.
