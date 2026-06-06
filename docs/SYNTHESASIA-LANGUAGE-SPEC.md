# Language Synthesasia — Triadic Symbolic Emotive Grammar

Updated: 2026-06-06
Status: v0.1 seed spec
Boundary: creative language / symbolic UX system; not a claim about universal language, cognition, or neurology.

## Canonical Rule

Synthesasia expresses emotion through three symbols or three-symbol groupings.

A Synthesasia unit is a triad:

```text
[Origin Symbol] [Motion / Tension Symbol] [Landing / Response Symbol]
```

The three symbols do not merely label emotion. They emote by showing where feeling begins, how it moves, and where it lands.

## Grammar

| Slot | Function | Example Role |
|---|---|---|
| 1. Origin | emotional source, initial state, signal seed | fear, wonder, grief, curiosity, warmth |
| 2. Motion | pressure, conflict, transformation, direction | opening, closing, splitting, spiraling, returning |
| 3. Landing | response, integration, rest, choice, boundary | safe, held, unresolved, released, protected |

## Example Triads

| Synthesasia Triad | Plain Reading | Notes |
|---|---|---|
| Lantern + Door + Home | Hope moves through threshold into safety. | Good base phrase for Dream Journal onboarding. |
| Static + Bug + Window | Nervous/chaotic signal tries to become visible. | Blinkbug-adjacent. |
| Key + Lock + Room | Hidden tension seeks permission and access. | Darkkey / threshold grammar. |
| Water + Stone + Garden | Emotion slows into grounded growth. | Calm / integration. |
| Fog + Wing + Mirror | Unclear feeling rises and reflects back. | Dream analysis phrase. |

## Syntax Notes

- A symbol may be visual, textual, emoji-like, glyph-like, color-coded, or grouped.
- A grouping can itself contain smaller motifs, but the top-level emotional structure remains three-part.
- Repetition changes intensity.
- Inversion changes valence.
- Missing third symbol means the emotion is unresolved.
- Missing first symbol means the origin is unknown.
- Missing second symbol means the emotional motion is blocked or not yet perceived.

## Dream Journal Integration

Each Dream Journal entry can store:

```json
{
  "synthesasia": {
    "origin": "Lantern",
    "motion": "Door",
    "landing": "Home",
    "plain_reading": "Hope moves through threshold into safety.",
    "confidence": 0.7,
    "source": "user-selected | inferred | agent-suggested"
  }
}
```

## Privacy / Consent Rule

If a Synthesasia triad is inferred from private dream content, it inherits the dream's privacy classification. Public demos must use synthetic dreams or user-approved examples only.

## Portfolio Framing

> Synthesasia is a small invented symbolic-emotive grammar for Dream Journal. It encodes emotional motion as three-symbol groupings, making private writing easier to tag, search, and revisit without flattening it into generic sentiment labels.

## Next Actions

1. Create a 30-symbol starter dictionary.
2. Define color and shape equivalents for accessibility.
3. Add user-selected triads to Dream Journal entries.
4. Add agent-suggested triads with editable confidence.
5. Add search by triad slot: origin, motion, landing.
