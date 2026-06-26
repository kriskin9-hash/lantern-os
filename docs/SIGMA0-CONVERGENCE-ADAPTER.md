---
author: Alex Place
created: 2026-06-25
status: Proposed
---

# Σ₀ Convergence Adapter — spec, data, eval, and the GPU program

> **What it is:** a fine-tune that makes a model *natively* perform the Σ₀ Convergence
> discipline — ground claims in evidence, tag `[claim · evidence · confidence · source]`,
> call tools to check rather than assert, verify before asserting, and **withhold
> confidence when evidence is missing** — without a giant system prompt. It is one
> swappable component of the (model-agnostic) Convergence loop, not a replacement for it.

This is the training counterpart to the runtime pieces already on master: verify-gated
escalation ([SIGMA0-OURO-CODER §escalation], #1197), the distillation flywheel (#1198),
and code-aware retrieval (#1200).

## The iron rule: verification-gated data, or you train hallucination

Teaching a model to *emit* "evidence: …, confidence: 0.9, source: …" is trivial format
mimicry. If the training traces aren't **verified**, you train the model to produce
convincing-looking evidence whether or not it's real — sophisticated hallucination in a
Σ₀ costume, which defeats the entire thesis.

**Therefore every training trace MUST be verification-gated:**
- **code** → the solution's tests/asserts actually ran green (executable check);
- **facts** → the cited source actually contains the claim (retrieval check).

This is the External Reality Rule applied to our own training data. No green check → not
a training row.

## Two modalities

| Adapter | Output discipline | Verify gate | Primary slot |
|---|---|---|---|
| **Coding/tools** (first) | concise, correct code + a one-line self-check; tool calls where needed | execute asserts/tests in a sandbox | the local 7B coder slot (#1207) |
| **Reasoning** (later) | grounded prose with `[claim·evidence·confidence·source]`; abstains w/o evidence | source-contains-claim check | the reasoning surface |

Start with **coding** — verification is objective (run the code), and it's the token-saving
slot. The "discipline" there is mostly *the gate on the data* (only verified-correct
solutions train) plus concise correctness, not verbose tagging that would hurt code.

## Training-example schema (matches `training-data.jsonl`)

```json
{
  "instruction": "<task>",
  "input": "<retrieved context / evidence, may be empty>",
  "output": "<verified Σ₀ solution>",
  "meta": { "source": "sigma0-distill", "teacher": "anthropic/claude-opus-4-8",
            "verified": true, "verify": "asserts-green", "ts": "..." }
}
```
`train-qlora-ouro.py` already reads `{instruction,input,output}`, so this drops straight in.

## Data sources (both verification-gated)

1. **The flywheel (real, free):** verified cloud rescues from live escalations →
   `data/distill/escalation-wins.jsonl` (#1198). Highest quality — real tasks on your
   distribution.
2. **Proactive teacher distillation (scales with the GPU/API budget):**
   `scripts/gen_sigma0_traces.py` — a frontier teacher solves a task under the Σ₀ system
   prompt, the solution is **executed against asserts**, and only green traces are kept.
   This is how a few-hundred-GPU-hours/week budget becomes a large verified corpus.

## Eval — prove it's *more Σ₀*, not just more verbose (define BEFORE training)

An adapter with no eval is an unfalsifiable GPU burn. Measure on a held-out set:

| Metric | What it catches |
|---|---|
| **pass@1** | raw capability didn't regress |
| **Calibration (ECE / Brier)** | stated confidence tracks actual correctness (the core Σ₀ property) |
| **Abstention rate on no-evidence prompts** | does it say "insufficient evidence" instead of fabricating |
| **Hallucinated-evidence rate** | cites sources/asserts that don't exist (must go DOWN) |
| **Format adherence** | emits the claim/evidence/confidence/source structure when asked |

Promotion gate: an adapter promotes only if pass@1 holds **and** calibration/abstention
improve. Same eval-gated discipline as `continual_ouro_pipeline.py`.

## The GPU program (uses the budget)

```
loop weekly (or faster):
  1. gen_sigma0_traces.py  — mint N verified traces from the teacher (verify-gated)
  2. merge flywheel + generated → training set
  3. train-qlora-ouro.py on the base (Qwen2.5-Coder-7B for product; Ouro for research)
  4. eval_sigma0_adapter.py — pass@1 + calibration + abstention + hallucination
  5. promote ONLY on a measured win; else keep incumbent
  6. ablate (data mix, rank, seq) — this is what the GPU hours buy
```

With hundreds of GPU-hours/week the leverage is **many runs + ablations + larger verified
corpora**, not one big run. The corpus is the moat (yours, on your distribution); the base
is swappable; the adapter is base-specific (retrain per base).

## Base model

- **Product:** `Qwen2.5-Coder-7B` (the local coder slot, #1207) — capability + fits the 3070 at 4-bit.
- **Research:** `Ouro-1.4B` — the looped-efficiency track; same corpus, separate adapter.

## Status
Proposed (needs Alex's approval to make it the canonical training track). Generator landed:
`scripts/gen_sigma0_traces.py`. Eval (`scripts/eval_sigma0_adapter.py`) is the next artifact.
Related: [SIGMA0-CONTINUAL-TRAINING.md], [SIGMA0-OURO-CODER.md], #1196/#1198/#1207.
