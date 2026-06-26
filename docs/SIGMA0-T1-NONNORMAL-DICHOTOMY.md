# Theorem 1 (non-normal) — the spectral-dichotomy extension

**Status: PROVEN in-regime + machine-checked (2026-06-26).** This closes the **contraction half
of [#768]**: Theorem 1's collapse-onto-the-manifold guarantee, which the
[Collapse Certificate](SIGMA0-COLLAPSE-CERTIFICATE.md) §1 proves only for **normal `A`**, now holds
for **non-normal `A`** via the spectral (Riesz) dichotomy. The C3 *anti-freeze* half of #768 is
separately closed (see [SIGMA0-C3-NONCOLLAPSE-NORMAL.md](SIGMA0-C3-NONCOLLAPSE-NORMAL.md) §7); this
doc is the **other** half — the *drift* question, not the *rescue*. With both halves closed, **#768
is closed**.

> **Scope of "PROVEN."** The §1 statements are closed-form modulo standard Lyapunov / exponential-
> dichotomy facts (Daleckii–Krein, Coppel). All three claims are machine-checked: the certificate
> is shipped (`src/cio_sde/collapse.py::dichotomy_certificate`), validated by a 600-matrix randomized
> sweep (`experiments/prove_t1_nonnormal_dichotomy.py`, 0 failures) and 3 suite tests
> (`tests/test_cio_sde.py::test_t1_nonnormal_{invariance,active_decays,dichotomy}`). "Machine-checked"
> = closed-form algebra + numerical sweep + pytest, **not** a Lean/Mathlib formal proof. The honest
> scope is unchanged: this is contraction of the **local linear Jacobian** onto its slow manifold,
> not a global non-collapse guarantee — grounding remains the safety mechanism.

---

## 0. The idea (why the symmetric split was the wrong tool)

Theorem 1 splits state space by the **symmetric part** `A_s = ½(A+Aᵀ)` (orthogonal eigenbasis) and
runs a Lyapunov energy `V = ½‖P_M x‖²` on the active modes. For non-normal `A` the cross-term
`P_M A P_N ≠ 0` (the §1.1 obstruction) breaks `V̇ ≤ 2αV`, and worse — §2 already notes the
`A_s`-null manifold isn't even invariant under the real flow. So "collapse onto the `A_s`-null
manifold" is genuinely **false** for non-normal `A`, not merely unproven. The `A_s` split is an
artifact that is exact only when `A` is normal (`A = A_s`).

**The fix: split by `A`'s own spectrum (the oblique Riesz projector), not `A_s`'s.**

---

## 1. Theorem (non-normal contraction dichotomy)

Let `ẋ = Ax`, `A ∈ ℝⁿˣⁿ` (possibly non-normal). Fix `δ > 0` with no eigenvalue on the line
`Re λ = −δ` (a spectral gap). Let `Π_M` be the **Riesz spectral projector** onto
`M = ⊕{generalized eigenspaces with Re λ < −δ}`, `N` the complementary invariant subspace
(`Re λ ≥ −δ`), `Π_N = I − Π_M`.

**(a) Invariance — the cross-term vanishes.** `AM ⊆ M`, `AN ⊆ N`, so `Π_M A = A Π_M` and hence
`Π_M A Π_N = 0`. The obstruction that defeats the §1 energy proof is *identically zero* in `A`'s
own spectral basis. *(Verified: `‖Π_M A − A Π_M‖ ≤ 3e-11` over 600 random non-normal `A`.)*

**(b) Active decay with bounded transient.** `A_M := A|_M` (the active block in an orthonormal
basis of `M`, `A_M = BᵀAB`) has spectral abscissa `< −δ` — Hurwitz. The Lyapunov equation
`A_Mᵀ P + P A_M = −I` has a unique `P ≻ 0`; with `V(ξ)=ξᵀPξ`, `V̇ = −‖ξ‖² ≤ −V/λ_max(P)`, so

> `‖Π_M x(t)‖ ≤ √(cond(P)) · e^{−t / (2 λ_max(P))} · ‖Π_M x(0)‖ → 0`.

The prefactor `√cond(P)` is the **transient overshoot**: for non-normal `A_M` it can be `≫ 1` but
is always finite, and is equivalently bounded by the Kreiss constant
`K(A_M) ≤ sup_t‖e^{tA_M}‖ ≤ e·n·K(A_M)`. *The active modes always die; non-normality shows up only
as a bounded overshoot, never as a failure to contract.*

**(c) Dichotomy — fate decided purely by the slow block.** Let `β = max{Re λ : λ ∈ spec(A_N)}`
(the slow-block spectral abscissa).
- `β > 0` ⟹ a mode in the open RHP ⟹ `‖x(t)‖ → ∞` (generic `x0`): **divergence**.
- `β ≤ 0` and `A_N` semisimple on the imaginary axis ⟹ `sup_t‖e^{tA_N}‖ < ∞` ⟹ `‖Π_N x(t)‖`
  bounded; with (b), `x(t) → N`: **collapse onto the center/slow manifold** (the generalized
  42-state).

By (b) the active part *always* decays, so only `sign(β)` decides the fate — **no third option**:
no trajectory both keeps the active part alive and avoids the collapse/diverge dichotomy.

**Caveat (the honest edge).** A *defective* (Jordan) eigenvalue exactly on `Re λ = 0` gives
polynomial growth — a measure-zero, non-generic boundary; conservatively classify it as
non-collapse. And `Π_M` is ill-conditioned when an eigenvalue sits within `~GAP` of the split line
`−δ`; choose `δ` in a spectral gap.

**Relation to Theorem 1.** For normal `A`, `A_s = A`, the Riesz projector *is* the orthogonal
`A_s`-projector, and this reduces to Theorem 1 exactly. So T1-NN is a strict generalization, and
Theorem 1 is its normal-`A` special case.

---

## 2. Evidence (machine-checked, 2026-06-26)

| Claim | Status | Artifact |
|---|---|---|
| (a) invariance — split is A-invariant, cross-term vanishes | **VERIFIED** — 0/600 failures, worst `‖(I−BBᵀ)AB‖ = 6.7e-13` | sweep + `test_t1_nonnormal_invariance` |
| (b) active decays within the certified Lyapunov envelope | **VERIFIED** — 0/600 envelope violations (worst obs/bound ratio 1.000), 0 active-not-decayed | sweep + `test_t1_nonnormal_active_decays` |
| (c) dichotomy, no third fate (fate = sign β) | **VERIFIED** — 0/600 fate mismatches (empirical slow-block growth rate's sign = sign β) | sweep + `test_t1_nonnormal_dichotomy` |
| small-gain `alpha` over-rejects these | shown (+26, +18, +8.7 on genuinely-contracting non-normal A) | `explore_nonnormal_contraction.py` |

`python experiments/prove_t1_nonnormal_dichotomy.py` → **VERIFIED** (600 random non-normal A,
d∈{4,5,6,8}). `pytest tests/test_cio_sde.py` → **42 passed** (the 3 T1 tests included). The shipped
certificate is `src/cio_sde/collapse.py::dichotomy_certificate`; it is surfaced at decode time via
`src/sigma0/loop_lm.py::_stability_gates` (the `"dichotomy"` field), reported alongside the #768
stability gates.

---

## 3. What was done (handoff completed 2026-06-26)

**3.1 Sweep rewritten with the correct numerics** (`experiments/prove_t1_nonnormal_dichotomy.py`).
The earlier check evolved the FULL propagator `e^{tA}·Π x0` (which amplifies projector roundoff in
the unstable direction, ratios ~1e38) and used `−max Re λ` as the envelope rate. Both fixed: each
block is evolved by its REDUCED dynamics in an orthonormal basis (`c(t)=e^{tAᴹ}c₀`, `d(t)=e^{tAᴺ}d₀`,
no leakage), the active envelope uses the valid Lyapunov bound `√cond(P)·e^{−t/(2λ_max(P))}`, and the
fate is validated by the SIGN of the slow block's empirical late-time growth rate (robust to β's
magnitude) rather than fixed ratio thresholds.

**3.2 `dichotomy_certificate(A, delta)` added** to `src/cio_sde/collapse.py` (+ `DichotomyCertificate`).
Returns `fate ∈ {COLLAPSE, MARGINAL, DIVERGE}`, `collapses`, `active/slow_dim`, `active_abscissa`,
`slow_abscissa = β`, `active_decay_rate = 1/(2λ_max(P))`, `transient_bound = √cond(P)`, and
`invariance_residual`. Uses the eig-based Riesz projector → orthonormal active basis, and the SAME
reduced Lyapunov metric as `stability_gates()` applied to the active block `A_M`.

**3.3 Three suite tests added** (`tests/test_cio_sde.py`): `test_t1_nonnormal_invariance`,
`test_t1_nonnormal_active_decays`, `test_t1_nonnormal_dichotomy` — all green.

**3.4 Wired into the decode-time check** — `loop_lm._stability_gates` now also reports the dichotomy
fate on the empirical decode Jacobian (purely diagnostic; the acceptance gate is unchanged). This doc
promoted DRAFT → PROVEN-in-regime; [SIGMA0-COLLAPSE-CERTIFICATE.md](SIGMA0-COLLAPSE-CERTIFICATE.md) §1
updated to move the #768 contraction frontier from open to closed-in-regime.

**3.5 Scope honesty (unchanged).** This is *contraction-onto-the-manifold for the local linear
Jacobian* — NOT a global non-collapse guarantee; grounding remains the safety mechanism. "Machine-
checked" = closed-form algebra + sweep + pytest, **not** Lean.

---

*Source of record for the math: this doc + `experiments/explore_nonnormal_contraction.py` (designed
cases) + `experiments/prove_t1_nonnormal_dichotomy.py` (randomized sweep) + the shipped
`dichotomy_certificate`. The reusable Lyapunov/Kreiss
machinery is `stability_gates()` in `src/cio_sde/collapse.py`.*
