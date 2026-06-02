# Dream Journal Skill

**Status:** Production-ready core module  
**Type:** Local-first, append-only, privacy-preserving  
**Integration:** Lantern Dreamer notebooks, MILD/WBTB protocols, SFI vectors, Bayesian World Model  

---

## Overview

The Dream Journal skill provides structured, local-only dream logging and analysis for Lantern OS. It coexists with (does not replace) the existing Discord-driven Dreamer system and produces high-quality mirror prompts for operator analysis and symbolic interpretation.

**Design principles:**
- Small, reviewable, functional on first import
- No skeleton — every function serves a real use case
- Append-only storage for audit trail and privacy
- Backward compatible with existing Lantern Dreamer notebooks

---

## Core Features

### 1. Structured Dream Logging

```python
from skills.dream_journal_skill.dream_journal import dream_journal

entry = dream_journal.log_dream(
    content="I was flying over a city made of light...",
    lucidity=0.7,  # 0.0–1.0 normalized (or /10 scale, auto-converted)
    emotions=["wonder", "clarity", "peace"],
    tags=["flying", "architecture", "clarity"],
    linked_goals=["understand_vision", "improve_lucidity"],
    sfi_impact={"meaning": 0.3, "purpose": 0.2, "character": 0.1}
)
# [OK] Structured dream logged: dream_20260602_143022_a1b2c3 (lucidity=0.70)
```

**Storage:** `data/dream_journal/dreams_YYYY-MM.jsonl` (one entry per line, JSON)

---

### 2. Retrieval & Analytics

```python
# Get the last 7 dreams
recent = dream_journal.get_recent(limit=7)

# Each entry contains:
# - id, timestamp, content, lucidity (0.0–1.0)
# - emotions, tags, linked_goals
# - sfi_impact: {meaning, purpose, character} (Symbolic / Flourishing Index)
# - source: "dream_journal_skill"
```

---

### 3. Mirror Prompt Generation (for Supergrok / Analysis)

```python
# Generate a grounded symbolic analysis prompt
prompt = dream_journal.mirror_prompt()

# Delivers:
# 1. Core symbolic pattern / recurring motif
# 2. Connection to waking-life goals or current tensions
# 3. One actionable insight for meaning/purpose/character
# 4. Bayesian uncertainty or missing context
# 5. One precise question for the dreamer to refine the model
```

Prompts follow the **Orion/Mookman Report 4** style: insightful, evidence-tethered, respectful, free of over-claiming.

---

### 4. Continuity with Existing Dreamer System (Read-only)

```python
# Scan existing Lantern Dreamer notebooks for 'dream' kind entries
dreamer_dreams = dream_journal.ingest_from_dreamer_notebooks(
    limit=20,
    user_filter=None  # e.g., "courtney" to filter by user
)

# Returns normalized entries from data/dreamer/notebooks/*.jsonl
# Does NOT write or modify existing dreamer data — read-only bridge only
```

**Backward compatibility:** Structured journal and Dreamer notebooks are unified in retrieval.

---

### 5. Bayesian World Model Hook (Stub)

```python
# Placeholder for future integration with Bayesian World Model skill
dream_journal.update_sfi_from_analysis(
    dream_id="dream_20260602_143022_a1b2c3",
    analysis={"meaning": 0.5, "purpose": 0.4, "character": 0.6}
)
# [held] SFI update received but not yet wired to world-model ledger
```

Contract is clear: when Bayesian World Model skill is ready, this hook will append belief-ledger style updates.

---

## Usage Examples

### Example 1: Log a lucid dream

```python
dream = dream_journal.log_dream(
    content="""I was in my childhood home, but it felt alive. The walls 
breathed with a soft blue light. I knew I was dreaming—full clarity. I 
decided to fly upward through the ceiling, and it felt natural, like 
gravity had reversed. I woke before reaching the sky.""",
    lucidity=0.9,
    emotions=["clarity", "control", "curiosity"],
    tags=["lucid", "childhood", "flying", "exploration"],
    linked_goals=["develop_lucid_dreaming", "understand_subconscious"],
    sfi_impact={"meaning": 0.5, "purpose": 0.3, "character": 0.7}
)
```

### Example 2: Generate a mirror prompt for analysis

```python
prompt = dream_journal.mirror_prompt()
print(prompt)
# Outputs a structured prompt asking for:
# - Core symbolic pattern
# - Connection to waking goals
# - Actionable insight
# - Bayesian uncertainty
# - Refining question for next entry
```

Then feed this to Supergrok or your preferred symbolic interpreter.

### Example 3: Bridge to Dreamer system

```python
# Get recent 'dream' entries from existing Lantern Dreamer notebooks
existing = dream_journal.ingest_from_dreamer_notebooks(limit=5, user_filter="courtney")
print(f"Found {len(existing)} recent Dreamer notebook entries")

# Use in unified analytics:
all_recent = dream_journal.get_recent(limit=7)  # From structured journal
# + existing dreamer entries for cross-reference
```

---

## Storage & Privacy

**Structured journal:** `data/dream_journal/dreams_YYYY-MM.jsonl`
- Append-only ledger
- Local-only (no cloud sync by default)
- JSON Lines format: one entry per line
- Audit trail: timestamp, source, user metadata (future)

**Dreamer notebooks:** `data/dreamer/notebooks/*.jsonl` (existing)
- Not touched by this skill
- Read-only ingestion for continuity
- Backward compatible

---

## Integration Points

1. **Lantern Garage Dashboard:** Dream Journal panel can call `dream_journal.get_recent()` and `dream_journal.mirror_prompt()`
2. **MILD/WBTB Skill:** Sibling skill can log lucidity milestones and track protocol effectiveness
3. **Bayesian World Model:** Future integration via `update_sfi_from_analysis()` hook
4. **MCP Tools:** Can expose `log_dream()`, `get_recent()`, `mirror_prompt()` as MCP tool calls
5. **Convergence Loop:** Can include dream analysis as part of daily/weekly evidence gathering

---

## Testing

```bash
python skills/dream_journal_skill/dream_journal.py
# [OK] dream_journal.py loads and basic methods functional
# Recent structured dreams: 0
# Recent dreamer 'dream' entries (sample): 0
# Mirror prompt available: True
```

---

## Design Notes

- **No skeleton:** Every method is implemented and functional. No placeholders except the Bayesian World Model hook (which has a clear contract for future work).
- **Small and reviewable:** ~200 lines of core logic, 100 lines of docs.
- **Privacy-first:** Append-only, local-only, no external APIs.
- **Symbolic discipline:** Mirror prompts follow Orion style: evidence-tethered, respectful of uncertainty, actionable.
- **Coexists with Dreamer:** Does not replace Discord-driven system; reads from it for continuity.

---

## Future Enhancements

- **Lucidity coaching:** Auto-suggest MILD/WBTB protocols based on lucidity trends
- **SFI correlation:** Link dream themes to character/meaning/purpose growth vectors
- **Pattern detection:** Identify recurring symbols, emotions, and their evolution
- **Dream-goal alignment:** Show connections between logged goals and dream content
- **Export & reports:** Generate monthly dream summaries for reflection

---

## Questions for the Operator

1. Should dream entries be encrypted at rest?
2. Do you want Discord integration to auto-log Dreamer entries to the structured journal, or keep them separate?
3. Should `linked_goals` pull from a shared goals list, or free-form entry?
4. Timeline for Bayesian World Model integration?
