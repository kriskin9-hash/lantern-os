# Ouro-1.4B → 70% HumanEval: Investigation & Findings (Issue #1292)

**Author:** Claude (autonomous training cycle)
**Date:** 2026-06-27
**Verdict:** **Negative for the planned levers.** LoRA fine-tuning the *general* Ouro-1.4B
does not beat its **35% held-out** base on HumanEval; recurrence-depth control is not a
usable lever. A genuine 70% appears to require a **code-pretrained 1.4B base**, not more
LoRA on Ouro. Every number below is **held-out (odd-indexed) and decontaminated**.

---

## TL;DR

| Approach | Held-out HumanEval pass@1 |
|---|---|
| Ouro-1.4B base + fixed harness | **35%** (the real bar) |
| LoRA on opencode (MBPP + CodeAlpaca) | 35.4% — tie |
| LoRA on 58,728 clean OSS-Instruct/Evol rows | **0–5% — regression** |
| Recurrence-depth control (`exit_at_step`) | n/a — default already optimal; forcing it breaks decode |

The on-model levers (data, depth) are **exhausted at ~35%**. The only remaining on-Ouro
lever is **test-time reranking**, realistically worth +10–20 pts (~45–55%), still short of 70%.

## Method & honesty protocol

- **Decontamination first.** `scripts/decontaminate_training.py` removes any training row
  sharing a 13-gram with HumanEval or MBPP (the BigCode/StarCoder standard). This caught
  real leakage in the open data — e.g. `fibfib` is literally HumanEval/63, and the prior
  in-house "self-study" had put 82 even-indexed HumanEval problems into training.
- **Held-out eval only.** Because even-indexed HumanEval problems had been used as
  self-study, the honest metric is **odd-indexed** problems (`--odd-only`), which the model
  never saw. The previously-celebrated "50%" was contamination: checkpoint-600 scored
  **50.0% on seen (even)** vs **35.4% on held-out (odd)** across the full 164.
- **Greedy decoding** for canonical pass@1; no fabricated metrics (Σ₀).

## Phase 0 — Decontamination (done)

`scripts/decontaminate_training.py` dropped 416/2509 (16.6%) from the prior opencode set
and 243/58,971 (0.4%) from the new OSS-Instruct/Evol set — including genuine HumanEval
overlaps. All subsequent training used decontaminated data.

## Phase 1 — Recurrence depth (negative)

Ouro is a LoopLM with trained depth `total_ut_steps=4`; `forward()` exposes `exit_at_step`,
`use_weighted_exit`, `exit_threshold`. We wired these into the eval (`--exit-at-step`,
`--weighted-exit`). Result on base Ouro, held-out:

| config | pass@1 | s/problem |
|---|---|---|
| default (= trained T=4) | 35.4% | ~82 |
| exit_at_step=1 | 5.0% | 4.3 |
| exit_at_step=2/3/4 | 0–0% | ~3.5 |

Forcing `exit_at_step` through the cached `generate()` path makes the model emit just
` ``` ` and halt (~4s vs ~82s). This is an **incompatibility with the fast cached decode**,
not "depth hurts": the default generation already runs at the trained peak. Going beyond
T=4 needs the no-cache Q-exit loop (infeasibly slow). **Depth dropped as a lever.**

## Phase 2 — OSS-Instruct + Evol-Instruct data (decisive negative)

Built a large, proven, raw-completion code set: Magicoder OSS-Instruct-75K +
evol-codealpaca-v1 → 58,971 first-function completions → **58,728 after decontamination**
(`scripts/prep_code_instruct.py`). Trained QLoRA (`max_steps=2500`, ~0.34 epoch, healthy
loss ~0.63 — no memorization). Held-out across checkpoints:

| checkpoint | epoch | held-out pass@1 |
|---|---|---|
| 900 | 0.12 | 5.0% |
| 1350 | 0.18 | 5.0% |
| 1950 | 0.27 | 0.0% |
| 2500 | 0.34 | 2.5% |

The model generates **runnable but logically-wrong, comment-heavy code** (27/40
AssertionError) — it absorbed the verbose OSS-Instruct/Evol *style* and lost accuracy.
More training did not recover. This data+format **actively harms** held-out HumanEval on
this base.

## Why this happens

A *general* 1.4B model has limited capacity for code-specific competence. LoRA can impose
a surface style but cannot install the reasoning that a code-pretrained model gets from
trillions of code tokens. The base model's general reasoning (35%) is, if anything,
*degraded* by style-tuning. For calibration: code-pretrained 1.4B-class models reach
65–70% (Qwen2.5-Coder-1.5B-Instruct ≈70%, DeepSeek-Coder-1.3B-Instruct ≈65%) — but their
*base* models are already ~35–43%, i.e. the gap is in pretraining, not the LoRA.

## Recommendation

1. **If 70% is the hard requirement:** use a **code-pretrained 1.4B base**
   (e.g. Qwen2.5-Coder-1.5B-Instruct) as the substrate. This is the only path that
   realistically reaches ≥70%; it is no longer "Ouro-1.4B".
2. **If staying on Ouro matters more:** implement **test-time reranking** (generate N
   candidates, select by the docstring's provided example assertions — *not* self-generated
   tests, which the literature shows bias/hurt). Honest ceiling ~45–55%.
3. **Do not** invest more GPU in LoRA-on-general-Ouro for HumanEval — three datasets now
   show tie-or-regress.

## Artifacts

- `scripts/decontaminate_training.py` — 13-gram decontamination vs HumanEval+MBPP
- `scripts/prep_code_instruct.py` — OSS-Instruct + Evol → raw-completion
- `scripts/eval_humaneval_ouro.py` — adds `--odd-only`, `--exit-at-step`, `--weighted-exit`
- Results: `data/eval/leaderboard.jsonl`; tracking: issue #1292
