# Orion / Mookman Report 4 Style

Status: active style spine  
Scope: Markdown, flat text, CSS, HTML operator surfaces  
Source visual: Lantern OS Orion Watch technical sheet  
Use when: rewriting Lantern OS public-safe reports, flat RAG files, README-style pages, and static surfaces

---

## Simple Answer

A Lantern OS document should read like a technical sheet, not a file dump.

The reader should see:

- what this page is;
- why it exists beyond the phone / repo / raw artifact;
- what it actually does;
- what is proven, held, or local-only;
- the next safe action;
- the validation path.

Do not lead with raw paths, command spam, generated chatter, or unbounded claims.

---

## Visual System

| Layer | Rule |
|---|---|
| Paper | warm white or limestone background |
| Lines | thin blue engineering-grid lines |
| Panels | rounded technical cards with clear headers |
| Accent | teal/cyan for live/usable, amber for held, red only for blocked |
| Geometry | tesseract / constellation motifs as light structure, not decoration spam |
| Icons | simple line icons or text labels only |
| Tone | direct, human-relevant, source-disciplined |

CSS tokens:

```css
:root {
  --orion-paper: #f7f8f4;
  --orion-ink: #0d1b26;
  --orion-muted: #526676;
  --orion-blue-line: #9fb9c9;
  --orion-blue-deep: #15384f;
  --orion-teal: #0e9f9b;
  --orion-cyan: #72e8e1;
  --orion-amber: #b98228;
  --orion-panel: rgba(255, 255, 255, 0.94);
  --orion-night: #071924;
}
```

---

## Markdown / Flat Text Shape

Every public-facing flat `.md` or `.txt` file should use this order unless there is a stronger operational reason not to:

1. `# Title`
2. metadata block: status, scope, source, validation state, operator boundary
3. `## Simple Answer`
4. `## What It Actually Does`
5. `## Evidence / Source Discipline`
6. `## Proven / Held / Local-Only`
7. `## Next Safe Action`
8. `## Validation Path`
9. appendices, paths, raw commands, receipts

Paths belong in the evidence or appendix section, not in the first screen.

---

## Mookman Report 4 Rules

The Mookman report pattern stays because it is human-readable and evidence-safe:

- Metadata first, but short.
- Executive summary before tables.
- Source discipline before claims.
- Confidence table for uncertain identity, state, or live-tool claims.
- No private identity claims without direct confirmation.
- No fake live state.
- No screenshot/image claim unless source, date, caption, and usage note exist.

Apply that pattern to Orion, RAG Dollhouse, Lantern Ring, Spanish Abode, Van, shipping leads, and any public-facing concept packet.

---

## CSS Surface Rules

For `styles.css` files:

- Use the Orion tokens above.
- Use blue grid/tesseract backgrounds lightly.
- Make cards scannable at 1080p and on phone.
- Keep focus outlines visible.
- Avoid hidden controls that look active.
- Disabled / local-only controls must visually read as held.
- Button text must say what action is real.

Required visual motifs:

```css
body {
  background:
    linear-gradient(90deg, rgba(21, 56, 79, 0.07) 1px, transparent 1px),
    linear-gradient(rgba(21, 56, 79, 0.07) 1px, transparent 1px),
    radial-gradient(circle at 18% 10%, rgba(14, 159, 155, 0.14), transparent 32%),
    var(--orion-paper);
  background-size: 32px 32px, 32px 32px, auto, auto;
}
```

```css
.orion-card,
.panel,
.system-panel {
  border: 1px solid var(--orion-blue-line);
  border-radius: 16px;
  background: var(--orion-panel);
  box-shadow: 0 14px 34px rgba(7, 25, 36, 0.08);
}
```

---

## Copy Rules

Use direct copy like:

> Phone = deep work. Orion = fast access. Together they reduce friction.

Use repo equivalents:

> Repo = evidence store. Surface = fast access. Together they reduce confusion.

Avoid:

- “perfect” unless validation actually passed;
- “live” unless the state was just checked;
- “ready” unless gates are green;
- large raw path blocks before the reader understands why they matter.

---

## Validation Path

For style-only changes:

```powershell
python -m pytest tests -q
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Invoke-LanternConvergenceLoop.ps1 -CloudVirtualization
```

For local surfaces:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Start-LanternGarageApp.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Open-TonyGarage.ps1
```

Manual checks:

- first screen has title, purpose, and simple answer;
- buttons are real links, local app actions, or clearly disabled;
- local-only evidence is marked held;
- mobile layout is usable;
- no raw filepath spam above the fold.
