# Lantern OS Repository Contract

**Status:** Phase C Phase 0 — Defining repo boundaries  
**Date:** 2026-06-01  
**Purpose:** Clear definition of what belongs in this repository

---

## What Lives Here (Product Code)

✅ **Code that ships or supports shipping:**
- `apps/lantern-desktop/` — Tkinter desktop app (ships)
- `apps/lantern-browser/` — Flask web UI (ships)
- `apps/lantern-kids/` — Age-gated variant (ships)
- `src/hff-api/` — Shared Flask utilities (supporting code)
- `src/voice_curator/` — Music library manager (ships)
- `src/discord_lounge_bot/` — Discord integration (ships)
- `gm-agent-orchestrator/` — Suzie orchestrator (ships)

✅ **Supporting infrastructure:**
- `scripts/` — Automation for local development and ops (watchdog, orchestrator supervisor)
- `tests/` — Test coverage for shipped code
- `docker/` — Container definitions for deployment
- `config/` — Configuration templates (non-secret)

✅ **Documentation that explains shipped code:**
- `README.md` — Product overview
- `CONTRIBUTING.md` — Contributor workflow
- `ARCHITECTURE.md` — System design
- `docs/STREAMS.md` — Active product streams
- `docs/LINEAR-WORKFLOW.md` — Operator training
- `docs/REPO-CONTRACT.md` — This document
- Inline code comments (for non-obvious logic)

✅ **Evidence and validation:**
- `DEPLOYMENT_VALIDATION_SUMMARY.md` — v1.0.0 production readiness report
- `tests/` — Test results and coverage reports
- `manifests/validation/` — Deployment evidence (linked to commits)

---

## What Does NOT Live Here (Deleted or Archived)

❌ **Mythology and narrative language:**
- Any files referencing TARDIS, spine, anchor, convergence, door, Keyman, Lantern doctrine, etc.
- Examples: `docs/TARDIS-*.md`, `docs/convergence-*.md`, `docs/anchor-*.md`, `scripts/Wake-Lantern.ps1`
- All mythology-named task files in `tasks/` directory

❌ **Overengineered concepts without implementation:**
- "Impossibility Engine" framing in code or docs
- "Court-admissible cryptographic proof" claims (keep signing utility, delete marketing)
- "Polymorphic Seed Registry" (empty registry files)
- Grandiose branding that doesn't match shipped code

❌ **Private and personal content:**
- Conversation logs (`.lantern/state/journal.jsonl`, `.lantern/state/convo-stream.jsonl`)
- Screenshots (`.lantern/state/screen-latest.png`)
- Personal journals or meditation notes
- Named personal references (Courtney, Gage, kickazzkenji, etc.)
- Therapy/medical/household stories
- Identifiable private data of team members

❌ **Stale documentation and outdated plans:**
- "500-year lab" grand-unified theory docs (refactor to Longevity Evidence Summary with citations)
- Multi-era architectural plans (keep only current design in ARCHITECTURE.md)
- "Perfect adjacent" reviews and handoff packets (move to Linear notes, not repo)
- Old roadmaps and obsolete timelines (keep current plan in README, move old to archive)

❌ **Broken or unfinished code:**
- Unmaintained scripts (e.g., `scripts/lantern-batch.ps1` if orphaned)
- Unfinished apps (e.g., `apps/toy-robot-lantern/` if no active development)
- Half-implemented features with TODO markers (finish before shipping)

❌ **Secrets and credentials:**
- Discord bot tokens (real or example)
- API keys for Claude, Gemini, GPT
- Database connection strings with passwords
- SSH keys or certificates
- Note: Use `.env` files (not tracked) for local secrets

❌ **Large binaries and generated files:**
- `.pyc` files (Python bytecode)
- Node modules (use `package.json` + npm/yarn)
- Virtual environment directories (use venv, don't track)
- Generated build artifacts (create during build, don't store)

❌ **Duplicate repository copies:**
- `C:\Users\alexp\Documents\hff-fresh\` (2026-05-12 snapshot)
- `C:\Users\alexp\Documents\hff-master-clean\` (stale copy)
- Other `.../orchestrator-local-backup-*/`, `../branch-archives/`, etc.
- One working tree per repo; others archived elsewhere, not in `.git`

❌ **Momentum docs and decision logs from manic periods:**
- Files that reference "manic phase", "crazy idea", "sketch this out"
- Grand unifying theory folders (BFT/mesh/blockchain plans without shipped code)
- Experimental features marked as "future vision" (use Roadmap section of README instead)

---

## Gray Zone (Case-by-case decision)

❓ **Optional reference docs:**
- `docs/REFERENCE_*.md` — Only if actively cited elsewhere
- Academic or patent papers — Only if shipped features depend on them
- Historical context docs — Only if Founder says it matters
- Deprecation notices — Only for features we shipped and removed

❓ **Experimental code:**
- Code tagged `TRL 2 (concept)` or `TRL 3 (lab)` — OK if it's in a subdirectory with clear README
- Example: `hff_distributed/` contains optional BFT library (no production requirement)
- Rule: Experimental code must have its own README explaining status, scope, and non-shipping nature

❓ **Stale branches:**
- Don't commit branches to master
- Use worktrees for exploration
- Archive feature branches in git (don't delete), not in the filesystem

---

## Application

### For Contributors

Before committing, ask: **Does this ship or help someone ship shipped code?**

- ✅ YES: Commit it (keep it organized, documented)
- ❌ NO: Delete it or move to a separate repo
- ❓ MAYBE: File an issue, ask Founder for decision

### For Cleanup (Phase C)

Use this contract as the **deletion checklist**:

1. **Phase 0 (Done):** Fix README + AGENTS.md (you're here)
2. **Phase 1:** Delete all mythology language files (~85 HFF docs, `lantern-os/lantern/` folder)
3. **Phase 2:** Strip overengineering claims, validate BFT library
4. **Phase 3:** Refactor Tier 3 docs (500-year-lab → evidence summary)
5. **Phase 4:** Document shipped code (STREAMS.md, OVERVIEW.md, fresh READMEs)

### For Future Contributions

- Check this contract before creating new files
- If your work doesn't map to "✅ What Lives Here," discuss with Founder first
- Don't accumulate mythology or stale docs — delete them as soon as they stop being useful

---

## Archive Migration → Google Drive

Historical artifacts, old manifests, and large generated files should not accumulate in the repo. Move them to Google Drive after each convergence cycle.

### What to Archive

| Category | Examples | Destination |
|---|---|---|
| Old reports | `archive/reports-YYYY-MM-DD/` | `Lantern-OS-Archive/reports/` |
| Old manifests | `archive/manifests-*-YYYY-MM-DD/` | `Lantern-OS-Archive/manifests/` |
| Old skills | `archive/skills-YYYY-MM-DD/` | `Lantern-OS-Archive/skills/` |
| Old surfaces | `archive/surfaces-YYYY-MM-DD/` | `Lantern-OS-Archive/surfaces/` |
| Large PDFs | `*.pdf` > 5MB in `docs/` or `reports/` | `Lantern-OS-Archive/pdfs/` |
| Cleanup snapshots | `archive/root-cleanup-YYYY-MM-DD/` | `Lantern-OS-Archive/cleanup/` |

### How to Archive

```powershell
# Step 1: Run the archive commons batch to prepare folders
powershell -File .\scripts\Invoke-ArchiveCommonsBatch.ps1

# Step 2: Open Google Drive folder "Lantern-OS-Archive"
# Step 3: Drag the dated archive folders from archive/ to the Drive folder
# Step 4: Delete the local copies after confirming upload
# Step 5: Commit the cleaned archive/ state
```

### Rules

- Never delete from `archive/` without first confirming the files are in Drive.
- Keep the `archive/` directory itself — it's the staging area.
- Run archive cleanup at the end of every convergence cycle (after PR merge).

---

## Decision Tree

```
Does this file help someone ship code?
    ├── YES (code, tests, docs that explain code)
    │   └── Keep it, organize well
    ├── NO (mythology, stale plans, private content)
    │   └── Delete it or move to archive
    └── MAYBE (reference doc, experimental code)
        └── Ask Founder, or move to separate repo with clear status
```

---

## Files in Scope for Phase C Cleanup

### To Delete (Mythology)
- `docs/TARDIS*.md`, `docs/spine*.md`, `docs/anchor*.md` (20-30 files)
- `docs/convergence*.md`, `docs/door*.md`, `docs/echo*.md` (20-25 files)
- `docs/operator-*.md`, `docs/keystone-*.md`, `docs/lantern-*.md` (15-20 files)
- `docs/perfect-adjacent*.md`, `docs/seven-*.md` (10-15 files)
- `scripts/Wake-Lantern.ps1`, `scripts/help_lantern_now.ps1`, etc. (5 files)
- `gm-agent-orchestrator/lantern/` folder (entire directory)
- `tasks/` queue files with mythology names (~70 files)

### To Refactor (Tier 3 docs)
- `docs/500-year-lab*.md` → `docs/longevity-evidence-summary.md` (validate citations, apply GRADE)
- `docs/regulatory-primitive-stack.md` → draft synthesis note (compare against NIST AI RMF)
- BFT/mesh implementation → validate as TRL-2 optional library (`hff_distributed/`)

### To Document (Tier 1 streams)
- Create `docs/STREAMS.md` (catalog of active product streams)
- Create `docs/OVERVIEW.md` (polished 1-page writeup for reviewers)
- Update `CONTRIBUTING.md` (point to Linear, explain commit model)
- Update `README.md` (done: replaced old "unified" story with Lantern + Suzie)

---

**Last Updated:** 2026-06-01  
**Owner:** Founder (Operator) + Team (all contributors)  
**Next Review:** 2026-06-14 (Phase C Phase 1 completion)

---

## Quick Checklist

Before committing a file to master:

- [ ] Does it help ship code or help someone ship code? (YES: keep, NO: delete, MAYBE: ask Founder)
- [ ] Does it contain mythology language (TARDIS, spine, anchor, etc.)? (YES: remove, NO: continue)
- [ ] Does it contain private/personal data or secrets? (YES: delete, NO: continue)
- [ ] Is it in the appropriate directory? (Check directory structure above)
- [ ] Is there a clear purpose documented? (For new files, add context in PR)
- [ ] Have stale copies been removed? (No duplicate repos or backup folders)

If all checks pass: **commit it.**
