# Recent Models Research Intake Receipt

**Status:** held intake receipt  
**Date:** 2026-05-28  
**Source:** uploaded chat note named `Research on Recent Models.txt`

## Operator decision

Open a pull request instead of merging directly to `master`.

Reason: the chat-visible artifact is a short handoff note, not the full markdown report. It names the intended report contents but does not itself contain enough source text, citations, benchmark tables, or validation detail to promote directly into the release line.

## Captured note summary

The uploaded note says a research report was updated with additional sources and confidence assessments. It says the report highlights recent benchmark results for OSWorld, ClockBench, and SWE-bench Verified, details adoption of MCP and AGENTS.md, and discusses local-first agent frameworks such as goose.

## Claimed research coverage

The note says the full markdown report covers:

- recent OSWorld benchmark results;
- ClockBench results;
- SWE-bench Verified results;
- MCP adoption;
- AGENTS.md adoption;
- local-first agent frameworks such as goose;
- additional sources and confidence assessments;
- at least three independent references per claim.

## Boundary

This receipt does **not** claim that the full report has been imported, validated, or source-checked inside this repository.

Held until one of the following is true:

1. the full markdown report is attached as a retrievable artifact;
2. the full report is pasted into a candidate file;
3. a connector-visible durable file URL is supplied;
4. a local operator-machine handoff confirms the report path and checksum.

## Safe next action

Replace this receipt with the full report or add the full report beside it at:

```text
reports/RECENT-MODELS-RESEARCH-2026-05-28.md
```

Then run the convergence loop evidence checks before promotion:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Invoke-LanternConvergenceLoop.ps1
python .\scripts\Test-ConvergenceAgentFleet.py --write-json .\manifests\validation\CONVERGENCE-FLEET-LATEST.json
```

## Validation state

- GitHub remote write path: available.
- Local MCP health: held.
- Dirty worktree state: held.
- Full report contents: held.
- Citation/source verification: held.
- Merge readiness: not ready for direct master merge.
