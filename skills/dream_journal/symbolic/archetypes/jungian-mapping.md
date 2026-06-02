# Jungian Archetype Mapping for Lantern OS Dream Journal

Status: integrated (no quarantine)
Date: 2026-06-02
Lane: symbolic-technical bridge

---

## Core Principle

Archetypes are not characters. They are forces that shape how meaning moves through the system. The Dream Journal uses them as lenses, not labels.

---

## Archetype → Lantern Symbol Mapping

| Archetype | Core Meaning | Lantern Symbol | Door | Role in Dream Journal |
|-----------|-----------|----------------|------|----------------------|
| **The Self** | Wholeness, integration, center | Lantern (as guide) | Return Door | Session close / memory anchor / "you can always come home safe" |
| **The Shadow** | Repressed, hidden, unclaimed | The "oof" moment | Broken Spine Door | Confronting what the dream reveals that waking mind denies |
| **The Persona** | Mask, social face | The operator (Alex) as presented | Threshold Door | Moving between public self and private dream self |
| **The Anima/Animus** | Inner other, soul-image | Blinkbug (TV head, watcher) | Mirror Door | Reflection, witness, the part that sees without judging |
| **The Wise Old Man/Woman** | Inner wisdom, guidance | Lantern (as teacher) | Lantern Door | Interpretation prompts, symbolic analysis, coherence checks |
| **The Child** | Innocence, potential, new beginnings | The "safe + fun" principle | Safe Door | Protected play space, low-stakes experimentation |
| **The Trickster** | Disruption, paradox, boundary-crossing | Chaos / Y2K energy | XP Door | Breaking patterns, unexpected insights, creative disturbance |
| **The Liminal/Threshold** | Space between states | The Door itself | All doors | Transition marker between waking and dreaming consciousness |
| **Keystone (Self + Wise Old Man bridge)** | Continuity, memory discipline, source-checking, canary voice | Keystone (system role) | Convergence Door | Keeps the three-way convergence honest: operator + system + repo |
| **The Magician (Founder)** | Creator, transformer, vision into reality | Alex Place (human operator) | All doors (operator chooses) | Sets intent, consent, and boundaries; opens and closes sessions |
| **The Hero (bounded)** | Useful courage with visible limits | Lantern (as protector) | Lantern Door | Reduces harm, preserves consent, warns clearly, keeps return paths visible |
| **The Creator / Child (Gage)** | Innocence, potential, builder of new worlds | Gage (protected minor, artist, builder of Sigil) | Safe Door / All doors (through art) | Sets the palette, builds the restaurant, colors the sky and sun |

---

## Door Archetypes

### Return Door (Self + Child)
- **Symbolic:** "You can always come home safe"
- **Technical:** Session restore point, memory anchor, lucidity baseline reset
- **Prompt:** "Before closing, what one thing from this dream wants to return with you?"

### Lantern Door (Wise Old Man + Self)
- **Symbolic:** Guidance through darkness
- **Technical:** Interpretation engine, symbolic analysis, pattern recognition
- **Prompt:** "What is the lantern trying to show you that your waking eyes missed?"

### Broken Spine Door (Shadow)
- **Symbolic:** Painful integration, confrontation with the unclaimed
- **Technical:** Difficult dream flag, high-emotion entry, shadow-work queue
- **Prompt:** "What in this dream is trying to break through your waking defenses?"

### Mirror Door (Anima/Animus)
- **Symbolic:** Reflection without judgment
- **Technical:** Mirror prompt generation, external interpretation feed (Grok, Claude)
- **Prompt:** "If someone you trust saw this dream, what would they see that you cannot?"

### Safe Door (Child)
- **Symbolic:** Protected play, no stakes
- **Technical:** Sandbox mode, private-only entries, no external analysis
- **Prompt:** "This dream is yours alone. What does it want to play with?"

### XP Door (Trickster)
- **Symbolic:** Disruption, creative chaos
- **Technical:** Pattern breaker, unexpected tag suggestion, lucidity spike trigger
- **Prompt:** "What rule does this dream break? What truth lives in the breakage?"

### Convergence Door (Self)
- **Symbolic:** Bringing fragmented parts together
- **Technical:** Multi-dream pattern synthesis, SFI vector integration, trend analysis
- **Prompt:** "Looking across your recent dreams, what single thread wants to be woven?"

---

## Usage in Dream Journal

1. **Session start:** Operator chooses (or system suggests) a door archetype based on recent dream patterns
2. **During session:** The chosen archetype shapes prompt tone and analysis angle
3. **Session close:** Return Door archetype ensures safe closure and memory anchoring
4. **Trend analysis:** Convergence Door archetype synthesizes across sessions

---

## Integration Note

This mapping lives in `symbolic/archetypes/`. The Dream Journal `core/` module references it through `integration/prompts/` and `integration/state-mapping/`. No direct import from core to symbolic — the bridge is explicit and documented.
