# Student-size eval — Ouro-1.4B vs 7B coder (#1199)

**Date:** 2026-06-25 · **Where:** Lightning L4 (fp16) · **Bench:** HumanEval, N=10 (small/fast)
**Mode:** base-vs-base (no adapter) — fast raw-capacity signal, independent of the in-flight adapter.

| Model | pass@1 (N=10) |
|---|---|
| `ByteDance/Ouro-1.4B` (base) | **10%** (1/10) |
| `Qwen/Qwen2.5-Coder-7B-Instruct` (base) | **90%** (9/10) |

## Verdict
A 7B coder is **dramatically** more capable than Ouro-1.4B on coding (1/10 → 9/10). The
gap is far larger than any adapter could close, and **Qwen2.5-Coder-7B fits the RTX 3070
at 4-bit (~5 GB)** — so the capability ceiling for "recreate the cloud locally" is set by
student size, and 7B is the lever.

## Caveats (honest)
- N=10 is tiny (as requested: small/fast). The 1-vs-9 gap is decisive despite wide CIs, but
  re-run with `--n 50`/`--full` before any irreversible decision.
- HumanEval is function-completion — Qwen-Coder's strong suit. The agentic/repo-diff
  distribution (what escalation actually produces) may narrow the gap somewhat.
- Ouro-1.4B's value is the *looped-efficiency* research thesis (collapse certificate, Q-exit),
  not raw pass@1. This eval answers "capacity", not "is the Ouro research worth it".

## Recommendation
For the **local-cloud parity** goal: serve **Qwen2.5-Coder-7B (4-bit) on the 3070** as the
student, and point the distillation flywheel (#1198) at it. Keep Ouro-1.4B as the
efficiency-research track. This is an architectural fork (the Σ₀ looped thesis is
Ouro-specific) — **needs Alex's call** before reorienting serving/training.
