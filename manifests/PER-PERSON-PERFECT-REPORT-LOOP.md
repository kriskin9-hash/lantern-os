# Per-Person !perfect Report Loop

This loop makes each report evolve by person profile instead of using one static template.

## Inputs
- Profile: `profiles/<personId>/profile.json`
- Evolution log: `profiles/<personId>/report-evolution.jsonl`
- Live evidence: wallet and ledger files under `data/wallet/`

## Command
```powershell
cd C:\tmp\lantern-os
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\New-PerfectProfileReport.ps1 -PersonId founder -ReportTitle "COMET LEAP Founder Perfect Report" -RenderPdf
```

## Outputs
- Markdown: `reports/COMET-LEAP-<PERSONID>-PERFECT-REPORT-<YYYY-MM-DD>.md`
- PDF: `artifacts/COMET-LEAP-<PERSONID>-PERFECT-REPORT-<YYYY-MM-DD>.pdf` (when `-RenderPdf`)
- Evolution entry appended each run.

## Evolution Rule
Each run should:
1. Re-read that person's `profile.json`.
2. Pull current local evidence (wallet/ledger).
3. Append a new evolution event with snapshot values.
4. Generate a new dated report artifact.

This preserves history and lets tone/sections/goals diverge per person over time.
