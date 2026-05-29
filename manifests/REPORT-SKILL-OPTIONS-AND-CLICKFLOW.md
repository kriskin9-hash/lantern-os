# Report Skill Options + Clickflow (MCP/Chat Agents)

Purpose: expose multiple report-skill modes, show preview-ready choices, and
prefer click-selection over typed freeform input in chat UX.

## Option Catalog

| Option ID | Name | Renderer | Best Use |
|---|---|---|---|
| `light_mono` | Light Monochrome | `scripts/Build-PerfectArtPdf.founder-v4.ps1` | default clean reports |
| `dark_wcag` | Dark WCAG | `scripts/Build-PerfectArtPdf.founder-v4.dark.ps1` | high-contrast dark reading |
| `dark_noopacity` | Dark No Opacity | `scripts/Build-PerfectArtPdf.founder-v4.dark.noopacity.ps1` | dense art, no blending |
| `print_bw_pretty` | Print B/W Pretty | `scripts/Build-PerfectArtPdf.print-bw-pretty.ps1` | black-ink physical print |
| `founder_locked_v4` | Founder Locked v4 | `scripts/Build-PerfectArtPdf.founder-v4.ps1` | fixed founder style baseline |

## Click-First Chat Procedure

1. Agent provides 3-5 option cards with:
   - option id
   - one-line impact
   - expected output path pattern
2. User selects by click/tap choice in MCP chat UI.
3. Agent confirms selected option and runs the matching renderer.
4. Agent returns artifact link + validation result.

Rule: if click choices are available, do not force typed style prompts.

## MCP Integration Notes

- For MCP chat agents, publish option cards from
  `manifests/report-skill-options.json`.
- Keep typed fallback only when click UI is unavailable.
- Keep result payload compact:
  - selected option id
  - source report
  - output pdf
  - validation status

## Moderation/Governance

- Do not auto-promote claims from style-only changes.
- Keep evidence classes visible in report body.
- Preserve wallet factuality rules in all templates.
