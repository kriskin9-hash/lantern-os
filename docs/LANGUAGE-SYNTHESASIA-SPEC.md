# Language Synthesasia — Concept Specification

Status: concept definition, operator-authored  
Repo: `alex-place/lantern-os`  
Created: 2026-05-31  
Author: Alex Place

---

## Simple Answer

Language Synthesasia is a constructed personal language where every word or
meaning is encoded through exactly **three simultaneous references**. The name
blends *synthesis* (combining parts into a whole) with *synesthesia* (perceiving
one sense through another). Meaning is never a single symbol — it is the
intersection of three.

---

## What It Actually Does

### The Language

A Synthesasia expression is a **triad**: three references that together locate
one meaning. Each reference can be drawn from any channel the speaker chooses:

| Channel Type | Example Triad | Meaning (speaker-defined) |
|---|---|---|
| Temporal | past · present · future | "where something was, is, and will be" |
| Emoji | 🔥 · 🌊 · 🌱 | "destroy, cleanse, regrow" |
| Sensory | red · loud · rough | a texture of experience |
| Causal | cause · state · effect | how a thing moves through time |
| Relational | self · other · context | perspective anchor |

The triad is the atomic unit. A sentence in Synthesasia is a sequence of triads.
The reader resolves meaning by finding the intersection of all three references,
not by decoding any single one.

### 3-Point Simple Binary Search

The 3-Point Simple Binary Search is the **lookup method** for reading or
resolving Synthesasia expressions. It works like this:

```text
Given an unknown meaning M and three reference points (R1, R2, R3):

1. Compare M against R1 — yes/no: does M share qualities with R1?
2. Compare M against R2 — yes/no: does M share qualities with R2?
3. Compare M against R3 — yes/no: does M share qualities with R3?

The combination of three binary answers (2³ = 8 possible states)
locates M in a meaning space of up to 8 regions.
```

Each reference point gives a binary signal (yes/no, present/absent,
resonates/doesn't). Three binary signals together create a unique address in
an 8-cell meaning grid:

| R1 | R2 | R3 | Region | Interpretation |
|:---:|:---:|:---:|:---:|---|
| 0 | 0 | 0 | 0 | none of the three — outside the language |
| 1 | 0 | 0 | 1 | only R1 — rooted in first reference alone |
| 0 | 1 | 0 | 2 | only R2 — rooted in second reference alone |
| 1 | 1 | 0 | 3 | R1 + R2 — overlap of first and second |
| 0 | 0 | 1 | 4 | only R3 — rooted in third reference alone |
| 1 | 0 | 1 | 5 | R1 + R3 — overlap of first and third |
| 0 | 1 | 1 | 6 | R2 + R3 — overlap of second and third |
| 1 | 1 | 1 | 7 | all three — full convergence, strongest meaning |

Region 7 (all three match) is the **convergence point** — the meaning the
speaker intended. Regions 1–6 are partial matches that help the listener
triangulate. Region 0 means the expression doesn't map to the chosen triad.

---

## Relationship to Existing Lantern Patterns

The Arc Reactor 12-Step Convergence Model already uses a 4-column frame:

```text
Past Work → Present Pitch → Expected Future → Actual Result
```

Synthesasia compresses this to 3 references and generalizes beyond temporal
framing. The 4th column (Actual Result) becomes the **resolution** — what
happens when you apply the 3-point search and find where meaning lands.

| Lantern Pattern | Synthesasia Equivalent |
|---|---|
| Past Work | R1 — first reference (origin, history, anchor) |
| Present Pitch | R2 — second reference (current state, action) |
| Expected Future | R3 — third reference (direction, potential) |
| Actual Result | Region number — where the 3-point search lands |

---

## Examples

### Temporal Triad

```text
Triad: [yesterday · now · tomorrow]
Expression: [built the garage · shipping the demo · users arrive]
3-Point Search: R1=yes R2=yes R3=not yet → Region 3 (past+present, future pending)
```

### Emoji Triad

```text
Triad: [🔧 · 🎯 · 🚀]
Expression: [tool · aim · launch]
3-Point Search: R1=yes R2=yes R3=yes → Region 7 (full convergence — ready to ship)
```

### Mixed Triad

```text
Triad: [fear · clarity · motion]
Expression: [I was stuck · I see the path · I haven't moved yet]
3-Point Search: R1=yes R2=yes R3=no → Region 3 (aware but not acting)
```

---

## Evidence / Source Discipline

- **Origin:** Operator-defined concept, first recorded 2026-05-31.
- **Prior art:** No direct match found in any Lantern repo (`lantern-os`,
  `lantern-symbolic-sandbox`, `gm-agent-orchestrator`,
  `human-flourishing-frameworks`).
- **Related pattern:** Arc Reactor Past→Present→Future→Actual (4-column).
- **Related repo:** `lantern-symbolic-sandbox` — quarantine sandbox for
  symbolic language experiments (may host future Synthesasia expansions).

---

## Proven / Held / Local-Only

| Aspect | Status |
|---|---|
| Concept definition | proven (operator authored) |
| Formal grammar | held — needs worked examples and iteration |
| Machine parsing | held — no parser exists yet |
| RAG integration | held — could map triads to RAG evidence anchors |
| Public documentation | local-only until operator promotes |

---

## Next Safe Action

1. Review this spec for accuracy and completeness.
2. Decide whether to expand with a formal grammar (triad syntax rules).
3. Optionally move expanded symbolic work to `lantern-symbolic-sandbox`.
4. Consider mapping Synthesasia triads onto the Arc Reactor convergence model
   as an alternative 3-point view.

---

## Validation Path

- Operator reviews spec and confirms definitions match intent.
- If promoted: register in RAG dollhouse flat file and workstream list.
- If expanded: create worked examples in `lantern-symbolic-sandbox/symbols/`.
