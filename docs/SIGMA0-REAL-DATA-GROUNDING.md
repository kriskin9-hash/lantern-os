# Σ₀ Real-Data Grounding — the parrot attractor on a real log

*Closes #507 (epic #509). Realizes the deprecated §6/Appendix-A router
demonstration (#504) on a real, committed log using the shipped Σ₀ machinery,
the small-gain certificate (#505), and the surprise monitor (#506).*

- **Script:** [`experiments/sigma0_real_data_grounding.py`](../experiments/sigma0_real_data_grounding.py)
- **Artifact:** [`data/sigma0_real_data_grounding_report.json`](../data/sigma0_real_data_grounding_report.json)
- **Run:** `python experiments/sigma0_real_data_grounding.py` (seeded, no network)

§6 of the certificate was deprecated because its two driver scripts were never
committed and its "parrot attractor" numbers were hand-entered. This runs the same
idea on a **real, checked-in log** with the **committed** operators and writes a
logged artifact — the honest, reproducible version of that demo.

## Pipeline (encode → detect → excite → measure persistence)

1. **ENCODE** every turn of `apps/data/conversations/garage-conversations.jsonl`
   into the §6/Appendix-A state vector `x = [novelty, self_repeat, echo, length] ∈
   [0,1]⁴`, via token-set Jaccard over a sliding window.
2. **DETECT** — fit a local least-squares Jacobian `A` per window and run
   `collapse_certificate(A)` (the α / null-dim trajectory, #505), plus a Kalman
   `SurpriseMonitor` over the real series for the NIS / spook timeline (#506).
3. **EXCITE** — from the most-contracted real window's Jacobian, roll out the
   dynamics with Σ₀⁻¹ off vs on and measure the injected excitation and the
   sustained null-subspace energy.
4. **REPORT** — write the JSON artifact with an explicit real-vs-synthetic
   provenance block.

## Results (run of 2026-06-15, 2318 turns)

| Quantity | Value | Grounding |
|---|---|---|
| Trajectory means | novelty 0.52 · **self_repeat 0.46** · echo 0.15 | REAL |
| Parrot-attractor signature | **True** (high self-repeat) | REAL |
| Windows certificate-flags contracting | 22 / 2294 (first @ turn 24) | REAL |
| Rank+flatness proximity proxy | **never fires** (state stays full-rank) | REAL |
| NIS surprise spooks (threshold 12.49) | **1093** (first @ turn 2) | REAL timing |
| Σ₀⁻¹ excitation on real null mode | mean‖dx_extra‖ = 0.097 (p=0.25) | REAL mode, synthetic ξ |
| Null-subspace energy, on / off | **1.67×** (0.477 vs 0.285) | — |

## What is real vs synthetic (honesty contract)

- **REAL (grounded in the log):** the state-vector encoding, the fitted Jacobians,
  the certificate verdicts, and the *timing* of NIS surprise spikes.
- **SYNTHETIC (modeling choices):** the Kalman `R`/`Q` noise scales (they set the
  *magnitude* of NIS, not its timing), the excitation noise `ξ`, and the
  intervention rollout itself.
- **NOT AVAILABLE for a passive log:** two of the four Σ₀ trigger conditions
  (`∇ₓL` and `∂H/∂u`) need a control/optimization model. A passive log has none, so
  the proximity signal here uses only the two **data-observable** conditions —
  rank deficiency and Σ flatness — and the intervention is driven by the Jacobian's
  real null-fraction. This is stated, not hidden.

## What surprised us

1. **The log does not hard-collapse under this encoding.** The state stays
   full-rank and anisotropic, so the rank+flatness proximity proxy is 0 throughout —
   there is no 4-condition Σ₀ "42-state" freeze here. The parrot signature shows up
   instead as *high self-repeat* (0.46), not as a rank collapse.
2. **Surprise fires constantly (1093 spooks).** Real conversation turns are far less
   predictable, step-to-step, than the fitted linear model's `R`/`Q` allow — the NIS
   χ² test is chronically tripped. The *timing* is real; the absolute rate is a
   function of the (synthetic) noise scales and should not be over-read.
3. **Σ₀⁻¹ works on a real null mode, but effective-rank is the wrong yardstick.**
   The operator injects measurable excitation along the one real flat direction and
   sustains 1.67× the null-subspace energy. Because the null space is 1-D, that
   energy concentrates in a single direction and *lowers* naive effective rank —
   null-subspace energy, not rank, is the faithful metric here. The baseline never
   freezes, so this demonstrates **persistent excitation**, not a rescued collapse.

## Relation to the epic

- **#504** — this is the honest, reproducible realization of the deprecated §6 demo.
- **#505** — uses `collapse_certificate()`'s small-gain bound on the fitted (non-normal) Jacobians.
- **#506** — uses `SurpriseMonitor` (NIS) on real observations.
- **#508** — the certificate doc's status boxes can now cite this run as the §6 real-data follow-up.
