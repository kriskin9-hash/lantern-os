# Race Condition Convergence

Generated: 2026-05-26.

Status: applied to local Lantern OS repo.

Purpose: make the repo safer under parallel agents, browser requests, PDF
builds, and batch validators.

## Global Rule

```text
stream first, batch second, queue same-file writes, dry-run external changes
```

## Fixed In This Pass

| Surface | Risk | Fix |
|---|---|---|
| PDF builder | Shared temp Python filename could race during parallel PDF builds. | Use per-process GUID temp filename and cleanup. |
| !perfect art PDF builder | Needed art-backed pages without shared temp races. | Add `Build-PerfectArtPdf.ps1` with per-process GUID temp filename. |
| Discord dry run | Shared temp Python filename could race during repeated dry runs. | Use per-process GUID temp filename and cleanup. |
| Conversation intake | Concurrent POSTs could interleave same-file JSONL writes. | Serialize appends through per-file write queue. |
| RAG cache intake | Concurrent POSTs could interleave same-file JSONL writes. | Serialize appends through per-file write queue. |
| Flat RAG snapshot | Concurrent snapshot writes could overlap. | Serialize writes per target path. |
| Validation | Single write checks missed race behavior. | Add concurrent batch POST validation. |
| Frontpage | Normies handout was not exposed from the Garage page. | Add `Normies Handout` link to Pages panel. |

## Pattern

Use JSONL streams for intake:

- conversations;
- RAG cache;
- wallet events;
- belief ledger rows.

Use bounded batches for derived artifacts:

- reports;
- PDFs;
- flat RAG snapshots;
- validation receipts;
- public handouts.

Do not raise confidence from a derived batch unless the source stream and
validation receipt are visible.

## Held

This pass does not claim every possible race in every source repo is fixed.
It fixes the known local Lantern OS races found in this loop and records the
pattern future agents must follow.
