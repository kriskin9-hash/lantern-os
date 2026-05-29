---
name: comet-leap-print-wcag
description: Format COMET LEAPER and Lantern OS reports for WCAG-readable, black-and-white-safe, print-ready, and !perfect art-backed PDFs. Use for founder reports, ADR/ADS reviews, whitepapers, operational guides, handouts, and public/normie packets that need polished PDF output without losing accessibility or evidence labels.
---

# COMET LEAPER Print + WCAG + Art PDF

Use this skill from `C:\tmp\lantern-os` when preparing reports, ADRs, ADS
reviews, whitepapers, handouts, or any `!perfect` PDF.

## Core Rule

The Markdown source is the accessible source of truth. The PDF may add art,
texture, page framing, and foreground memory marks, but the art must not carry
meaning that is absent from the text.

## Web-Grounded Constraints

- WCAG 2.2: keep text readable, preserve heading structure, avoid color-only
  meaning, and provide text equivalents for meaningful non-text content.
- ADR practice: architecture decisions must stay easy to review through status,
  context, decision, and consequences.

## !perfect Art Edition

When the operator asks for `!perfect`, finished PDFs, art on each page, or a
report redesign:

1. Always use `scripts/Build-PerfectArtPdf.ps1` (ReportLab path).
2. Use repo-owned art under `skills/lantern-rag-dollhouse/assets/images/`.
3. Put art in low-opacity background or small foreground thumbnail treatment.
4. Keep all text inside a high-contrast readable panel.
5. Keep evidence classes, decision states, and warnings as text.
6. Do not rely on color or art alone to show status.
7. Validate the PDF with `scripts/Validate-PerfectReportDesign.ps1`.
8. For per-person reports, run `scripts/New-PerfectProfileReport.ps1` so profile learning and evolution logs are updated every time.
9. For founder dark-theme packets, use `scripts/Build-PerfectArtPdf.founder-v4.dark.ps1` with white text on dark panels and high-contrast accent colors.

## Founder Dark + RAG House Standard

When the user asks for dark style, founder top-level, or RAG-house prominence:

1. Keep text `white-on-dark` with WCAG-friendly contrast.
2. Keep accent colors visible in headers, grids, and separators.
3. Keep RAG-house repo tables near the top third of the document.
4. Keep the tesseract dot-line layer decorative only, never replacing text meaning.
5. Validate with `scripts/Validate-PerfectReportDesign.ps1` and include a new artifact filename.

Example:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Build-PerfectArtPdf.ps1 -Source reports/ADS-ARCHITECTURE-REVIEW-v0.1.md -Output artifacts/ADS-ARCHITECTURE-REVIEW-v0.1.pdf
```

## Typography

- Body: 11-12pt for print when possible, never tiny in dense panels.
- Headings: clear hierarchy with one H1, then H2/H3 in order.
- Code/data: Courier or another monospace font.
- Letter spacing: normal; do not compress.
- Avoid decorative fonts and long italic blocks.

## Contrast And Print

- Prefer black or very dark text on white or very light panels.
- Tables may use light gray header fills and dark borders.
- Avoid color-only status.
- Keep the PDF readable when printed in black and white.

## Layout

- Single-column by default.
- Use tables for decisions, evidence maps, confidence, and next actions.
- Use page art as a background/foreground layer, not as content.
- Avoid nested cards, clutter, and huge decorative sections.
- Every page should have page number, local source, and report identity.

## ADR/ADS Report Shape

For architecture reports, include:

| Section | Purpose |
|---|---|
| Status | Proposed, accepted, held, superseded, or rejected. |
| Context | Forces, constraints, evidence, and why a decision is needed. |
| Decision | The chosen path in active language. |
| Consequences | Benefits, tradeoffs, risks, and held boundaries. |
| Evidence | Local files, validation output, official sources, or operator assertions. |
| Next Proof | The smallest validation that changes confidence. |

## COMET LEAP Report Shape

Use:

```text
past work -> present pitch -> expected future outcome -> actual result ->
evidence class -> confidence -> decision -> next proof
```

## Validation Checklist

Before calling a report finished:

1. Run `git diff --check` on changed Markdown/scripts.
2. Render the PDF.
3. Confirm the PDF file size increased or changed as expected.
4. Confirm local serving returns HTTP 200.
5. Extract at least the first page of text or inspect with a PDF reader.
6. Run relevant skill validators.
7. Run `node apps\lantern-garage\validate.js` when frontpage links changed.

## Boundaries

- Do not hand-edit generated PDFs.
- Do not overwrite private/raw image dumps into public reports.
- Do not inflate claims to make the design feel stronger.
- Use new artifact names when overwriting a tracked PDF would blur evidence.
