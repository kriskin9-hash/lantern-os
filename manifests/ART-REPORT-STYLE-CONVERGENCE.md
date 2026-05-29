# Art Report Style Convergence

Generated: 2026-05-26.

Status: applied to local Lantern OS repo.

Web grounding:

- WCAG 2.2: visuals cannot be the only carrier of meaning; text contrast,
  headings, labels, and non-text alternatives remain the accessibility spine.
- ADR practice: architecture decisions need status, context, decision, and
  consequences; art should frame the decision, not replace it.

Repo style:

```text
semantic Markdown source -> evidence-labeled tables -> !perfect art PDF render
```

## Page Rule

Every `!perfect` PDF page may include:

- low-opacity background art from repo-owned assets;
- a small foreground art thumbnail;
- a white readable content panel;
- page number, local path, and remote path footer.

Every `!perfect` PDF page must keep:

- black/dark text on light background;
- semantic headings in the Markdown source;
- evidence classes and decision states as text;
- no color-only meaning.

## First Targets

| Report | Source | Output | Status |
|---|---|---|---|
| ADS Architecture Review | `reports/ADS-ARCHITECTURE-REVIEW-v0.1.md` | `artifacts/ADS-ARCHITECTURE-REVIEW-v0.1.pdf` | regenerated with art style |
| Lantern OS Whitepaper | `reports/LANTERN-OS-WHITEPAPER-v0.1.md` | `artifacts/LANTERN-OS-WHITEPAPER-v0.1.pdf` | regenerated with art style |
| Day One Normie Packet | `reports/LANTERN-DAY-ONE-NORMIE-PACKET.md` | `artifacts/LANTERN-DAY-ONE-NORMIE-PACKET.pdf` | generated with dedicated large-art handout style |

## Day One Large-Art Handout

The Day One normie packet uses a dedicated renderer and generated abstract art:

```text
scripts/Generate-DayOneNormieArt.ps1
scripts/Build-DayOneNormiePdf.ps1
reports/assets/day-one-normie/
```

The packet format is:

```text
cover -> what it is/is not -> package cards -> token/time logic -> savings -> signoff
```

Each package keeps:

- plain version;
- pro version;
- Day One win.

## Validation

Use:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Build-PerfectArtPdf.ps1 -Source reports/ADS-ARCHITECTURE-REVIEW-v0.1.md -Output artifacts/ADS-ARCHITECTURE-REVIEW-v0.1.pdf
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Build-PerfectArtPdf.ps1 -Source reports/LANTERN-OS-WHITEPAPER-v0.1.md -Output artifacts/LANTERN-OS-WHITEPAPER-v0.1.pdf
```
