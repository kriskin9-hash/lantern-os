---
name: lucid-dreaming
description: MILD and WBTB protocol implementation for Lantern OS. Practical techniques, intention generators, reality-check scaffolding, and scheduling helpers. Designed to increase dream lucidity scores that feed the Dream Journal skill and Bayesian World Model.
---

# Lucid Dreaming Protocols (MILD + WBTB)

Status: active development (codex/dream-journal-structured)  
Scope: operator personal practice tools for lucid dream induction; integration points for Dream Journal and daily templates  
Source: classic LaBerge MILD research + WBTB field reports, adapted to Lantern OS evidence and flourishing frame  
Validation: module loads cleanly; protocols expressed as executable generators + documentation

## Simple Answer

A focused skill module that gives you concrete, repeatable MILD (Mnemonic Induction of Lucid Dreams) and WBTB (Wake Back To Bed) procedures. It generates personalized intention statements, reality-check prompts, and timing guidance that increase the probability of lucidity. Results (lucidity scores, dream reports) flow naturally into `skills/dream_journal/`.

## What It Actually Does

- `generate_mild_intention(last_dream_summary, personal_goals)` — Produces a concise, present-tense mnemonic phrase for use during the WBTB window and at sleep onset.
- `wbtb_schedule(sleep_time, target_wake_hours=5.5)` — Calculates recommended wake window, activity suggestions (reading dream journal, light movement, no screens), and return-to-bed timing.
- `reality_check_prompts(count=5)` — Supplies varied, non-obtrusive reality checks (text, time, hands, environment, breathing) suitable for daytime practice and dream use.
- `daily_lucid_ritual_template()` — Returns a minimal daily structure (morning recall, daytime RC practice, evening intention setting) that can be dropped into `templates/daily/`.
- Clear boundaries: educational / personal-practice only. No claims of guaranteed lucidity or therapeutic outcomes.

## Evidence / Source Discipline

- Core techniques drawn from Stephen LaBerge's published MILD research and the lucid dreaming literature (standard, non-proprietary).
- Integration targets the existing Lantern Dreamer capture surface (`/dream` commands, `data/dreamer/notebooks/`) and the new structured `dream_journal` module.
- No new external dependencies. Pure Python + documentation.
- Held: large-N personal outcome data for the specific Lantern-adapted phrasing (operator must generate their own evidence via consistent practice + journal logging).

## Proven / Held / Local-Only

**Proven:**
- Standard MILD + WBTB are among the best-evidenced cognitive techniques for increasing lucid dream frequency in the literature.
- The module follows the same small, importable, no-magic pattern as `solo-mining/examples/` and other skills.

**Held (explicit boundaries):**
- Individual results vary widely (sleep architecture, consistency, dream recall baseline). This skill provides the protocol, not the outcome.
- Does not interface with hardware (EEG headbands, light cues, etc.) in v1.
- Does not modify sleep architecture recommendations beyond the classic 5–6 hour WBTB core.
- Not medical advice. Consult professionals for sleep disorders.

**Local-only:**
- All generation is deterministic or seeded from your own dream summaries and goals. Nothing leaves the machine.

## Next Safe Action

1. Read `mild_wbtb_protocol.py` and run its `__main__` demo.
2. Use `generate_mild_intention` with a recent dream from your journal.
3. Pick one reality check and practice it 5–10× during the day.
4. Tonight, run the WBTB schedule for your normal bedtime and log the outcome (even if non-lucid) using the Dream Journal skill the next morning.
5. After 3–7 nights, review lucidity trend via `dream_journal.get_recent()` + Bayesian World Model if wired.

## Validation Path

- `python -m skills.lucid_dreaming.mild_wbtb_protocol`
- Log at least three dreams (lucid or not) after using the generated intentions and have the mirror_prompt surface any increase in lucidity or dream vividness.
- Re-run the Lantern Convergence Loop; confirm no new issues introduced.
- Future: Add a small `tests/skills/test_lucid_dreaming.py` with property-based checks on intention length and schedule sanity.

## Appendix: Quick Reference

**Classic MILD core (LaBerge):**
While falling asleep, repeat a short phrase that includes the critical state ("Next time I’m dreaming, I will remember I’m dreaming") while vividly imagining a recent dream in which you became lucid.

**WBTB core:**
After 5–6 hours of sleep, wake for 20–60 minutes. Stay upright, read dream journal or this skill’s output, perform gentle reality checks, then return to bed with fresh MILD intention.

See `mild_wbtb_protocol.py` for the exact generators used in this skill.

Related skills: `dream-journal`, `bayesian-world-model`.
