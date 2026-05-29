# AGENTS

Status: active agent instruction file  
Repo: Lantern OS v1.0.0 staging  
Style spine: `docs/ORION-MOOKMANREPORT4-STYLE.md`

---

## Simple Answer

Agents working in this repo should make Lantern OS clearer, safer, and easier to validate.

Every change should move raw material toward an Orion-style technical sheet: clear purpose, real evidence, held boundaries, next action, and validation path.

---

## Operating Rules

- Inspect before editing.
- Keep changes small and reviewable.
- Do not import dirty worktree state blindly from source repos.
- Do not mutate boot configuration, partitions, firmware boot order, or disks.
- Do not claim v1.0.0 readiness without operator approval.
- Use the Innovator evidence method for promotion decisions.
- Do not stop at skeletons. If a loop finds actionable local issues, fix the first 2-4 before starting new expansion work.
- Retire deprecated surfaces as an explicit convergence step.
- Apply the Orion / Mookman Report 4 style to public-facing Markdown, flat text, and CSS.

---

## Source Repos

```text
C:\tmp\human-flourishing-frameworks-scan
C:\Users\alexp\Documents\gm-agent-orchestrator
```

Both may be dirty. Treat their working tree state as evidence, not as something to overwrite or reset.

---

## Promotion Criteria

An artifact can move into this repo when it has:

- source path;
- purpose;
- claim IDs or clear claim summary;
- validation status;
- blockers and rollback notes;
- operator approval status;
- human-readable first screen;
- no raw filepath spam above the first explanation.

---

## Flat Document Shape

Use this order for public-safe `.md` and `.txt` files unless the file has a stronger operational structure:

1. title;
2. short metadata block;
3. simple answer;
4. what it actually does;
5. evidence / source discipline;
6. proven / held / local-only;
7. next safe action;
8. validation path;
9. appendices, raw commands, paths, and receipts.

---

## CSS Surface Shape

For static surfaces, use the Orion style:

- limestone / warm white paper;
- thin blue grid lines;
- teal/cyan status accents;
- amber held-state accents;
- rounded technical panels;
- visible focus outlines;
- no fake active buttons;
- disabled controls clearly marked as local-only or held.

---

## Required Loop

Before meaningful work, run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Invoke-LanternConvergenceLoop.ps1
```

Then handle the first 2-4 reported issues in priority order. If an issue cannot be fixed safely, mark it held in `manifests/open-issues.md` with the reason.

---

## Branching

Use `codex/` branch names for agent work unless the operator asks otherwise.
