---
author: Claude (Keystone engineer)
created: 2026-06-25
status: findings
---

# GPU Training Pipeline Diagnosis — Why Ouro Fine-Tunes Weren't Landing

## TL;DR

Dispatching a real weekly training run exposed a chain of five bugs that had been
silently breaking the self-improvement loop. Each fix advanced the run one stage
further — `dispatch → dataset mount → model load → CUDA init → precision select`.
All five are fixed and on master. **The remaining blocker is not a bug: Kaggle's
free GPUs (P100 / T4) are pre-Ampere, and this Ouro QLoRA recipe needs bf16, which
requires Ampere (cc ≥ 8.0). The correct free target is Lightning AI's A10.**

## What "run it now" actually exercised

Triggering `/api/gpu-training/dispatch` for Kaggle ran the orchestration end to
end — dispatch, poll, convergence-logging all work. The *kernel execution* failed,
and reading each failure's log drove a sequence of fixes:

| Stage reached | Failure | Root cause | Fix (commit) |
|---|---|---|---|
| — (deploy gate) | every stable deploy rolled back | `routes/api-tools-log.js` exported an Express `Router()` instead of the server's `(req,res,url,deps)=>bool` convention; it threw `fn.apply is not a function` and 500'd `/api/convergence/health`, the exact endpoint the deploy health-check probes | `0e98dbfe` |
| dataset mount | `FileNotFoundError` in ~2 min | kernel looked for `training-data.claude-combined.json`; the Kaggle Dataset ships `.jsonl` | `225880ee` (probe both) |
| model load | `ImportError: cannot import name 'layer_type_validation'` | dispatch pinned `transformers>=4.40,<4.53`; Ouro-1.4B's `configuration_ouro.py` needs `layer_type_validation` (added 4.54+). The train script's own header already targets "the transformers 4.57 that Ouro's custom code requires" — the wrappers contradicted it | `b5c62465` (pin → 4.57) |
| CUDA init (4-bit) | `cudaErrorNoKernelImageForDevice` | hardcoded 4-bit QLoRA; bitsandbytes nf4 kernels are built for cc ≥ 7.5; Kaggle gave a P100 (cc 6.0) | `5e7e9e87` (skip 4-bit on cc < 7.5; Ouro-1.4B fits unquantized in 16 GB) |
| CUDA init (bf16) | `cudaErrorNoKernelImageForDevice` | `torch.cuda.is_bf16_supported()` **false-positives** on P100; the first bf16 op then crashes | `8b1475a0` (gate bf16 on cc ≥ 8.0) |

### The deploy-blocker was the most expensive

`api-tools-log.js` (landed in `4324920b`) sat *before* convergence-dispatch in the
route chain. Because the server calls every handler as `handler(req,res,url,deps)`,
a callable Express `Router` read its 3rd arg (`url`) as `next`, threw on
`next.apply`, and 500'd `/api/convergence/health`. The stable auto-deploy
(`C:\dev\deploy-stable-from-master.ps1`) health-checks *that* endpoint, so **every
deploy since this file landed silently rolled back**, pinning lantern-os.net on an
old commit (`98c6b338`) for ~2 days. Fixing it produced the first clean deploy in
days. Lesson recorded in agent memory: route modules must export a plain handler,
never an express Router.

## The strategic finding: Kaggle is the wrong GPU class

The v25 run log was decisive:

```
CUDA: True | base: ByteDance/Ouro-1.4B
precision: bf16
GPU cc: 6.0 | 4-bit QLoRA: False        <- arch-aware fix correctly disabled 4-bit
torch.AcceleratorError: CUDA error: no kernel image is available ...  <- bf16 on P100
```

The recipe (`scripts/train-qlora-ouro.py`) deliberately prefers **bf16**: its own
comment notes fp16 QLoRA on this reasoning LM overflows gradients to `nan`, which
clipping then bakes into a garbage adapter. **bf16 is Ampere-only (cc ≥ 8.0).**
Kaggle's free fleet is exclusively pre-Ampere:

| GPU | Arch | cc | bf16? | 4-bit? | Verdict for this recipe |
|---|---|---|---|---|---|
| P100 | Pascal | 6.0 | ✗ | ✗ | unusable (fp16 plain LoRA only → NaN risk) |
| T4 | Turing | 7.5 | ✗ | ✓ | runs 4-bit but fp16 compute → NaN risk |

So no amount of fixing makes Kaggle a *trustworthy* target — the hardware lacks
bf16. The fixes above stop the crashes (the pipeline now reaches the training loop
on whatever Kaggle assigns), but adapter quality on fp16 is not dependable.

### Where the successful past runs happened

Prior good Ouro adapters trained on **Ampere** GPUs — the local 8 GB RTX and
Lightning AI's **A10 (cc 8.6)** — both of which have native bf16. That is the
hardware this recipe was tuned for.

## Recommendation

1. **Make Lightning AI (A10) the primary automatable training target**, not Kaggle.
   Lightning is already wired (`scripts/lightning_dispatch.py`,
   `training-dispatcher.js`) but currently fails dispatch on a teamspace/owner
   inference bug in the Lightning SDK (`error_count: 3` in
   `data/pcsf/gpu-training.pcsf.json`: *"Neither name is provided nor can the user
   be inferred from the environment variable"*).
2. **Keep Kaggle as a crash-free fallback** for arch-tolerant jobs, but do not rely
   on it for bf16-sensitive adapters. The arch-aware fixes mean it degrades instead
   of crashing.
3. Optionally **prefer Ampere providers in the rotation** for this model: reorder
   `rotation_order` so Lightning (A10) leads, with Kaggle behind it.

## Status of the loop

- Observe / Act: orchestration dispatch + poll + convergence-logging — **working**.
- Verify: each fix validated against the live Kaggle kernel log (external evidence).
- The weekly scheduled task (`KeystoneWeeklyTraining`, Mondays 00:00 UTC) is live;
  it will now reach the training loop on Kaggle and will train cleanly once
  Lightning A10 dispatch is restored.

## Follow-up issue

Tracked separately: "Prefer Ampere GPU for Ouro training; restore Lightning A10
dispatch (Kaggle is pre-Ampere, bf16-incompatible)."
