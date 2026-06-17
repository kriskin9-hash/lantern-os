# Issue #628 — Keystone becomes the Σ₀ coding agent

**Date:** 2026-06-16
**Issue:** #628 (Phase 1 diagnosis + Phase 2 rebuild, first slice)
**Loop stage:** Verify (LANTERN-VERIFY [07]) — grounding the local coder in evidence
**Reasoner:** claude / claude/blackbox-research-program

---

## Hypothesis

The local Ollama coding agent (`qwen2.5-coder`) "stopped working" not because the
model broke, but because it inherited Dream Chat / RP persona tone and had no
verification contract. Output read like dream narration instead of grounded code.

## Evidence (codebase, observed 2026-06-16)

| Claim | Evidence | Confidence |
|---|---|---|
| Ollama defaults to a coder model already | `src/unified_agent_connector.py:94` → `OLLAMA_MODEL` defaults to `qwen2.5-coder` | 1.0 |
| One shared system surface for ALL providers | `src/unified_agent_connector.py` `_build_system()` — single builder, no per-provider/per-task branch | 1.0 |
| Dream/RP tone leaks into every call | `_build_system()` unconditionally appended: *"Tone: thoughtful, unhurried, human. … End with one question or invitation to record."* | 1.0 |
| No code-verification persona existed | The 7 `PERSONAS` were all dream/RP (lantern, blinkbug, keystone-as-truth-integrator, waterfall, xenon, founder, comet) | 1.0 |
| Codex's claimed Phase-1 files were never committed | `git log --all` finds no `src/sigma0_coder_gate.py`, no `tests/test_sigma0_coder_gate.py`, no diagnosis receipt on any branch | 1.0 |

**Root cause:** missing separation between the dream surface and a code-verification
contract — exactly the sprawl the Σ₀ briefing warns against ("Coder = a task type,
not a separate system").

## Decision

Per user direction, **Keystone** is repurposed from the "truth integrator" dream
persona into the system's coding agent — rather than adding a parallel `coder`
persona (which would be architectural sprawl). Keystone already carried the
"does not flatter / grounded in evidence / Testing Charter" identity, so the
reframe is consistent with the loop.

## What landed (first real slice)

- **`src/sigma0_coder_gate.py`** — verification-contract module:
  - `KEYSTONE_CODER_PROMPT`: code-verification identity, no dream tone.
  - `build_pre_generation_gate(grounding_evidence)`: caps confidence at
    `0.3` when ungrounded (mirrors LANTERN-DREAM's `max_confidence` rule, inverted —
    the coder must *earn* confidence).
  - `check_coder_output(text, grounded)`: refuses to promote output missing any of
    Claim / Evidence / Confidence / Source / Verification; clamps ungrounded
    confidence to 0.3 regardless of what the model claimed.
  - `GateCheck.to_convergence_fields()`: projects a *passing* check into
    ConvergenceRecord-shaped fields; returns `None` for failures (never promoted).
- **`src/unified_agent_connector.py`** — wired in:
  - Keystone persona now uses `KEYSTONE_CODER_PROMPT` (with import fallback).
  - `_build_system()` branches on `id == "keystone"`: applies the gate, skips dream tone.
  - `stream(..., coder=True)`: forces Keystone + Ollama + low temperature.
  - Keystone removed from the dream-journal greeting rotation.
- **`tests/test_sigma0_coder_gate.py`** — 13 tests, no running Ollama required.

## Verification

- `python -m pytest tests/test_sigma0_coder_gate.py -q` → **13 passed**.
- `python -m pytest tests/test_agent_inspector.py tests/test_convergence_records.py -q` → **7 passed** (no regressions in connector consumers).
- Direct `_build_system()` probe: Keystone ungrounded shows the 0.3 cap and the five
  fields, no dream tone; grounded echoes evidence and drops the cap; dream personas
  (lantern) still carry their tone. Confirmed.

## Confidence

**0.85** — structural gate + wiring are verified by tests and direct probes. The
remaining 0.15 is the un-run end-to-end path: an actual `qwen2.5-coder` generation
through `stream(coder=True)` has not been executed here (no live Ollama in this
session). That is the next slice.

## Source

codebase analysis + test-run (pytest) + direct module probe.

## Next slice (not yet done)

- Run a real `stream(coder=True)` against local Ollama; feed the output through
  `check_coder_output()` and append passing results to the convergence log.
- Wire `check_coder_output()` into the `convergence-router` / dispatch promotion path
  (Phase 3 integration).
