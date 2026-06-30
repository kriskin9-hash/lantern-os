# Adaptive Loop Gate (ALG) — continuous recurrent depth in [0, 2]

**Status:** Proposed (design only). Depends on **Stage 0 parity PASS** of the base
PLT forward (see [README](README.md)). The gate ships **default-off** so it cannot
affect parity. Decision record: extends **[ADR-0011](../../docs/adr/0011-proprietary-sigma0-base-model.md)**
(own the model); weight policy **[ADR-0010](../../docs/adr/0010-verify-gated-continual-learning-last-resort.md)**
(adapter-only, frozen base).

**Loop stage improved (Feature Gate):** **Reason** (adaptive recurrent depth — spend
compute only where the input needs it) and **Converge** (the learned halting signal
is a native convergence certificate, same role Ouro's Q-exit plays). Not sprawl: it
is an additive module on the existing PLT port — no new memory system, no new agent
ecosystem, no new serving path.

---

## 1. The idea in one line

LoopCoder runs the shared layer stack a **fixed** 2 times. ALG makes that depth a
**continuous, learned variable `d ∈ [0, 2]`** — the model decides, per input, how far
to loop, and stops early when it has resolved the token. The cap of 2 is not arbitrary:
the PLT result is that 0→1→2 improves while **>2 regresses** (positional mismatch), so
**[0, 2] is the empirically-validated safe band** and 2 is a hard ceiling.

## 2. Metaphor → mechanism (so the capability is trainable + measurable)

| North-star framing | Concrete, citable ML | Where it lives |
|---|---|---|
| "range 0–2" | effective loop depth `d ∈ [0,2]`, hard-capped at the validated ceiling | mixture/halt schedule |
| "quantum / superposition" | **soft mixture** of the 0/1/2-loop states: `out = Σ wₖ·hₖ` — differentiable, never a hard integer at train time | readout head |
| "koan" (sit until resolved) | **learned halting** (Adaptive Computation Time, Graves 2016) — stop looping when the halt head fires; this is exactly Ouro's learned Q-exit | per-loop halt head |

The capability must come from the gate being **trained and measured** (Stage 2 eval),
never from the framing. The framing is the north star; the math is the proof.

## 3. Base loop recap (what we hook)

From `KeystonePLTModel._run_loops` ([`modeling_keystone_plt.py:310`](modeling_keystone_plt.py)):

```
hidden = E                                  # token embeddings
for loop_idx in range(plt_num_loops):       # = 2
    if loop_idx > 0:
        hidden = emb_scale*E + hidden_scale*h_prev   # CLP recombine
    for layer in self.layers: hidden = layer(hidden, loop_idx, ...)
    hidden = self.norm(hidden)              # per-loop norm  → h₁ (idx0), h₂ (idx1)
return hidden                               # currently always h₂
```

So the loop **already materializes** `h₁` (normed, after loop 0) and `h₂` (normed,
after loop 1). We add a third cheap anchor `h₀ = norm(E)` (no layers) to let the band
reach 0. The states are comparable (all post-norm). ALG changes only **how the final
state is read out** of these — it does not touch the per-loop math.

## 4. The mechanism

Two formulations; we train with the soft one and deploy with the hard one (standard ACT
practice — smooth gradients at train, real compute savings at inference).

### 4a. ALG-mix (training surrogate — the "superposition")

Capture `H = [h₀, h₁, h₂]` (depths `[0,1,2]`). A tiny gate produces weights over them:

```
g  = Linear(5120 → 3)(  pooled(h₁)  )        # pooled = mean over non-pad tokens (per-seq)
w  = softmax(g / τ)                          # w ∈ Δ², the 3-simplex
out = w₀·h₀ + w₁·h₁ + w₂·h₂                  # the "superposed" output
d  = w₁·1 + w₂·2                             # expected depth ∈ [0,2]  (reported metric)
```

Always computes both loops at train time, so gradients reach every branch. A **ponder
cost** `λ·d` pulls the gate toward shallow depth wherever it doesn't hurt the task loss —
that pressure is what teaches "use 2 only when you must."

### 4b. ALG-halt (inference — the "koan", real speedup)

After each available state, a halt head emits a probability; accumulate and stop:

```
p₀ = σ(Linear(norm(E)))                      # cheap: can we answer at depth 0?
  if Σp ≥ 1−ε  → emit h₀, STOP               # skip the whole stack on easy tokens
run loop 0 → h₁;  p₁ = σ(Linear(h₁))
  if Σp ≥ 1−ε  → emit h₁, STOP               # skip the 2nd pass
run loop 1 → h₂;  emit h₂                     # hard cap at 2
```

Per-**sequence** halting first (one depth for the forward, gated by a pooled signal) —
simplest, and already a clear win on short/easy prompts. Per-**token** halting
(Universal-Transformer style: halted positions freeze, others keep looping) is the
Stage-1b refinement once per-sequence is verified.

## 5. New parameters — adapter-scale, base frozen (ADR-0010)

Everything ALG adds is tiny and trainable on the 3070 in 4-bit (base frozen → only these
carry gradients):

- `loop_gate`: `Linear(hidden_size → 3)` + an `RMSNorm` on its input  (~15K params)
- `halt_head`: `Linear(hidden_size → 1)` reused at each boundary       (~5K params)
- a learned scalar temperature `τ` and (optional) `LoRA` on the existing per-layer
  `self_attn.plt_gate` if eval shows the global/local mix also needs nudging.

## 6. Config knobs (default-off ⇒ parity-identical)

Add to `KeystonePLTConfig`:

```python
plt_adaptive       = False        # OFF ⇒ forward is byte-identical to today → parity-safe
plt_loop_min       = 0
plt_loop_max       = 2            # the validated ceiling; never raise without a re-run
plt_adaptive_mode  = "halt"      # "mix" (train) | "halt" (infer)
plt_halt_threshold = 0.99        # 1−ε
plt_ponder_cost    = 1e-2        # λ on expected depth
```

With `plt_adaptive=False` the readout returns `h₂` exactly as now — **the parity gate
cannot be broken by code that is switched off.**

## 7. Integration sketch (the only forward change)

In `_run_loops`, accumulate the per-loop states and, if adaptive, read out via the gate:

```python
h_outs = [self.norm(E)]                       # h₀ anchor (depth 0)
for loop_idx in range(cfg.plt_num_loops):
    ... existing loop body ...
    hidden = self.norm(hidden)
    h_outs.append(hidden)                      # h₁ then h₂
if not cfg.plt_adaptive:
    return hidden                              # unchanged path (parity)
return self.alg.readout(h_outs, E)             # mix (train) / halt (infer) + depth metric
```

`self.alg` is a separate `nn.Module`; the base layers are untouched.

## 8. Training

- Freeze base; train `loop_gate + halt_head + τ` (+ optional LoRA) only.
- Loss `= CE(task) + λ·E[d]`. Data: the HumanEval-optimized coding corpus + FC sets
  already in the repo.
- 4-bit base + adapter fits the 8 GB 3070 (only the small heads have grads).

## 9. Eval gate (External Reality Rule — flips `verified:true`)

ALG is promoted **only** when, on HumanEval + MBPP (harnesses already in
[BENCHMARKS.md](../../docs/BENCHMARKS.md)):

1. it **beats fixed-1-loop** (proves the 2nd loop earns its compute), **and**
2. it **matches-or-beats fixed-2-loop** (proves adaptivity costs no accuracy), **and**
3. **mean depth < 2** (proves a real compute win — the whole point).

Miss any one → stays `verified:false`, does not lead. Only on a pass does
`apps/lantern-garage/lib/local-model-registry.js` flip to `verified:true` and the model
register as a Σ₀ council member with `selfConverges:true` (the halt head is its
convergence certificate).

## 10. Staged plan (ordering is non-negotiable)

| Stage | What | Gate | Where |
|---|---|---|---|
| **0** | Download Apache-2.0 weights; prove the **base** fixed-2-loop forward matches the vLLM reference | `top1_agree ≈ 1.0` (bf16, ≥24 GB cloud); 4-bit load-smoke first on the 3070 | `download_and_patch.py` → `check_parity.py` |
| **1** | Implement ALG (default-off), train the adapter (mix→halt) | adapter converges; depth metric sane | this doc |
| **2** | Eval vs fixed-1 / fixed-2 | §9 three-part gate | `eval_humaneval_chat.py` |
| **3** | Serve OpenAI/Ollama-compatible; wire `local-model-registry` | live in keystone chat | serving stage |

**You cannot train a gate over a forward you have not verified.** Stage 0 blocks Stage 1.
The ALG code can be written in parallel (it's inert until `plt_adaptive=True`), but it is
not trained or trusted until parity passes.
