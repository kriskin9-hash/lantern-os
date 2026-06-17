# Σ₀ Real-Data Grounding Demo — 1-Page Report

**Issue:** #523 (closes #507) · **Epic:** #509 · **Date:** 2026-06-15
**Run:** `python experiments/sigma0_real_data_grounding.py` (seed=7, no network)
**Artifact:** `data/sigma0_real_data_grounding_report.json`

---

## What was run

The committed Σ₀ machinery (small-gain `collapse_certificate()` from #505, Kalman
`SurpriseMonitor` from #506, `AntiCollapseOperator`) executed end-to-end on a
**real** conversation log — `apps/data/conversations/garage-conversations.jsonl`
(2,344 turns) — through the full **detect → excite → reground** loop.

Each turn is encoded into the §6/Appendix-A state vector
`x = [novelty, self_repeat, echo, length] ∈ [0,1]⁴` via token-set Jaccard over a
24-turn sliding window. Local linear Jacobians are fit per window; the certificate
and a Kalman NIS surprise monitor run over the real series; the most-collapsed
window drives a Σ₀⁻¹ anti-collapse intervention.

---

## Metrics (REAL)

| Metric | Value |
|--------|-------|
| Turns / state vectors | 2,344 |
| Mean novelty / self_repeat / echo | 0.517 / 0.459 / 0.145 |
| Parrot-attractor signature | **True** |
| Certificate windows | 2,320 |
| Collapse-guaranteed windows (α<0) | 22 (first @ turn 24) |
| NIS spook threshold | 12.49 |
| NIS spooks | 1,120 (first @ turn 2) |
| Intervention window | ends @ turn 230 (α=−0.406, null_dim=1) |
| Σ₀⁻¹ excitation `mean‖dx_extra‖` | 0.097 |
| Null-subspace persistence (on/off) | **1.674×** |

---

## Theory comparison

**Matched arXiv findings:**

- **Model collapse present** — parrot-attractor signature confirmed
  (self_repeat=0.46). *Shumailov et al., Nature 2024; Dohmatob et al., arXiv:2402.07043.*
- **Small-gain certificate certifies contraction** on non-normal real Jacobians
  (22 guaranteed windows). *Lohmiller & Slotine 1998.*
- **NIS canary detects model-reality mismatch** (1,120 spooks). *Bar-Shalom et al. 2001.*
- **Σ₀⁻¹ sustains the flat direction** at 1.674× the un-excited baseline — the
  "mix real data (π>0) to prevent collapse" mechanism. *Dohmatob et al., arXiv:2402.07043.*

**Diverged (and why):**

- **State-covariance proximity proxy never fires (max=0.0).** The real log stays
  full effective rank; collapse is detectable via the fitted-Jacobian null
  structure, not the state covariance. The idealized 4-condition Σ₀ gate is not
  reproducible on a passive log (∇ₓL and ∂H/∂u need a control model) — only 2 of
  4 conditions are observable. *Stated, not hidden.*
- **Baseline does not hard-freeze** (eff_rank stays 4 with Σ₀⁻¹ OFF). Full
  collapse is predicted only under purely recursive synthetic training (αt→0); a
  real mixed-source log is not purely self-referential, so it shows persistent
  excitation rather than a rescued collapse — consistent with arXiv:2402.07043's
  π>0 (real-data) branch.

**Verdict:** The Σ₀ machinery reproduces the qualitative model-collapse
phenomenology on a REAL log. Quantitative collapse magnitude diverges from the
synthetic-training regime because the log is not purely recursive — exactly the
real-data branch the theory predicts.

---

## Provenance (honesty contract)

- **REAL:** state encoding, fitted Jacobians, certificate verdicts, NIS spike timing.
- **SYNTHETIC (modeling choices):** Kalman R/Q noise scales (set NIS magnitude, not
  timing), excitation noise ξ, rollout dynamics + initial spread.
- **NOT AVAILABLE for passive logs:** 2 of 4 Σ₀ trigger conditions (∇ₓL, ∂H/∂u)
  require a control model; the proximity proxy uses only rank-deficiency and Σ-flatness.
