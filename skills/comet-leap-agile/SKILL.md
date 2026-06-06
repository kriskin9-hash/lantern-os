---
name: comet-leap-agile
description: COMET LEAP agile methodology skill for turning past Lantern convergence artifacts, master PDFs, Buffett/owner-earnings analysis, 30-day model evidence, and next-sprint decisions into an updated master report/PDF. Use when Codex needs to update the COMET LEAP master PDF, run the next agile convergence sprint, extract lessons from past convergence manifests, create confidence tables, or prepare shareholder/operator packets.
---

# COMET LEAP Agile

Use this skill from `C:\tmp\lantern-os` when updating the COMET LEAP master
PDF or planning the next agile convergence sprint.

## Core Rule

Do not start from a blank template. Read the past convergences first, then
update the master report and regenerate the PDF.

## Required Inputs

Read these before changing the report:

- `reports/COMET-LEAP-TOKEN-BURN-REVENUE-CONVERGENCE-v1.md`
- `artifacts/COMET-LEAP-TOKEN-BURN-REVENUE-CONVERGENCE-v1.pdf`
- `archive/reports-2026-06-04/COMET-LEAPER-OPERATING-NARRATIVE-v1.md`
- `skills/lantern-rag-dollhouse/assets/pdfs/COMET-LEAPER-OPERATING-NARRATIVE-v1.pdf`
- `manifests/comet-leap-30day-artifacts.md`
- `manifests/LOOP-2-SUMMARY.md`
- `manifests/LATEST-ADDS-CONVERGENCE.md`
- `manifests/FOUNDRY-MATRIX-RAG-DOLLHOUSE.md`
- `docs/CONVERGENCE-LOOP.md`
- `docs/INNOVATOR-EVIDENCE-METHOD.md`
- `docs/V1-READINESS-GATES.md`

## Agile Loop

1. Inspect `git status --short --branch` and remotes.
2. Run `scripts/Invoke-LanternConvergenceLoop.ps1`.
3. Read the required inputs above.
4. Identify the first 2-4 actionable gaps in the master PDF/report.
5. Split work into past, present, next sprint, and held boundaries.
6. Preserve evidence class on every claim:
   - verified local state;
   - source-repo evidence;
   - official web source;
   - operator assertion;
   - projection.
7. Use `skills/bayesian-world-model/SKILL.md` when a claim needs a prior,
   posterior, confidence drift, or durable belief-ledger row.
8. Update Markdown first.
9. Regenerate the PDF with `scripts/Build-MasterConvergencePdf.ps1`.
10. Validate PDF header, page extraction, and remote link.
11. Record what changed in `manifests/open-issues.md` or a dated convergence
    manifest.
12. Commit and push when validation passes.

## Arc Reactor 12-Step Model

When the operator asks for past work, present pitch, future outcomes, actual
results, Tony confidence, or Arc Reactor state, update:

```text
reports/ARC-REACTOR-12-STEP-CONVERGENCE-MODEL.md
reports/ARC-REACTOR-CONFIDENCE-READ.md
data/arc-reactor/status.json
```

Use this 12-step shape:

1. Past control-plane work.
2. Past COMET LEAP/PDF/art work.
3. Past RAG/memory work.
4. Present dual-boot/device state.
5. Present wallet/cash state.
6. Present offer/pitch state.
7. Present cockpit/surface state.
8. Present confidence/power-state.
9. Store/distribution lane.
10. Old repo/workstream intake.
11. Archive/commons/media rights lane.
12. Future fleet/server/device outcomes.

Each step must include:

- past work;
- present pitch;
- expected future outcome;
- actual result so far;
- confidence.

Do not raise confidence from ambition alone. Raise it only with local files,
commits, validation output, wallet events, store pages, users, cash, installs,
or runtime evidence.

## Master PDF Rules

The master PDF is generated from Markdown. Do not hand-edit the PDF.

Default source:

```text
reports/COMET-LEAP-TOKEN-BURN-REVENUE-CONVERGENCE-v1.md
```

Default output:

```text
artifacts/COMET-LEAP-TOKEN-BURN-REVENUE-CONVERGENCE-v1.pdf
```

Regenerate:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Build-MasterConvergencePdf.ps1
```

## Sprint Packet Shape

Every next-agile update should include:

- past convergence recap;
- current repo and artifact state;
- first 2-4 issues fixed this loop;
- money stream changes;
- local/server-farm token capacity policy;
- Matrix RAG/dollhouse changes;
- dual-boot and phone edge-node boundaries;
- 12 confidence frames when projections are involved;
- Arc Reactor 12-step table when past/present/future/result framing is needed;
- next sprint backlog with validation steps.

## Held Boundaries

- v1.0.0 release remains held until the operator explicitly approves it.
- Dual boot install remains held until physical operator action.
- True phone dual boot remains held until exact model, backup, boot path, risk,
  and rollback evidence are verified.
- Cloud token costs must use current official pricing; offline/server-farm
  Foundry tokens are unmetered internal capacity.
