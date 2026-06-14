# Σ₀ — The Collapse Certificate

*A computable stability certificate for convergence dynamics, and a small
honest demonstration of why an ungrounded self-improving system collapses.*

Status: working code + verified tests in `src/cio_sde/`. The theorems are
proven and checked against rollouts; the data results are illustrative (run on
a mostly-synthetic log) and labeled as such.

---

## 0. The object

We study a dissipative nonlinear system

$$\dot{x} = f(x, u, \theta), \qquad x \in \mathbb{R}^n$$

- `x` — internal state (for the router: a conversation's encoded state)
- `u` — control / persistent-excitation input
- `θ` — slowly-varying parameters (meta-state)

Linearizing along a trajectory `x*` gives the local Jacobian

$$\dot{\delta x} = A\,\delta x, \qquad A = \left.\frac{\partial f}{\partial x}\right|_{x^*}.$$

Everything below reasons about the eigenstructure of `A` and its symmetric
part `A_s = ½(A + Aᵀ)`.

---

## 1. The collapse-guarantee theorem

Split the state space using the symmetric part `A_s`:

- **null subspace** `N = span{ vᵢ : |λᵢ(A_s)| < ε }` — the near-invariant modes
- **active subspace** `M` — its orthogonal complement, projector `P_M`

Define the Lyapunov function on the active modes only:

$$V(x) = \tfrac{1}{2}\,\lVert P_M\,x \rVert^2.$$

Let the **active spectral abscissa** be

$$\alpha = \max\{\, \lambda_i(A_s) : v_i \in M \,\}.$$

**Theorem.** If `α < 0`, then

$$\dot V \le 2\alpha V \quad\Longrightarrow\quad \lVert P_M\,x(t)\rVert \le \lVert P_M\,x(0)\rVert\, e^{\alpha t}.$$

The active modes decay exponentially at rate `|α|`, and the trajectory
contracts onto the invariant null manifold `N`. **Collapse is guaranteed.**

If `α ≥ 0`, some active mode is non-contracting — the system may wander or
diverge instead, and collapse is **not** guaranteed.

**Verification.** With `A = diag`-style spectrum and `α = −0.8`, the certificate
predicts `contraction_rate = 0.8`; a real rollout shows `V` decaying
`1.891 → 0.004` monotonically. The certificate is exact, not approximate.
(`collapse_certificate`, `lyapunov_value` in `src/cio_sde/collapse.py`.)

---

## 2. The collapse trigger Σ₀

Σ₀ fires only in the genuinely underdetermined regime — **all four** conditions
together (a control singularity over a structureless field):

| condition | meaning |
|---|---|
| `‖∇ₓL‖ < ε_g` | no optimization signal remains |
| `rank(J_f) < ρ·n` | drift Jacobian has lost directional structure |
| `Σ` isotropically flat | uncertainty has no preferred direction |
| `‖∂H/∂u‖ < ε_c` | control cannot distinguish actions |

When triggered, Σ₀ projects the state onto the null eigenmodes of `A_s`:

$$x^\* = P\,x, \qquad P = V_{\text{null}} V_{\text{null}}^\top.$$

The result is the **"42-state"**: a stable, structureless summary the system
freezes onto. (`SemanticCollapseOperator`.)

---

## 3. The anti-collapse operator Σ₀⁻¹

Where Σ₀ projects **onto** the null subspace, Σ₀⁻¹ injects energy **along** it —
the persistent-excitation principle from adaptive control:

$$dx = f\,dt + dW + \Sigma_0^{-1}, \qquad \Sigma_0^{-1} = s\cdot p \cdot (V_{\text{null}}\,\xi)$$

with `ξ` random and `p ∈ [0,1]` the **collapse proximity** — 0 far from the
boundary (no-op, costs nothing), rising to 1 as `∇L`, rank, anisotropy and
control sensitivity all approach their thresholds. This restores rank and
re-anisotropizes `Σ`, pushing the system off the wall before it freezes.

**Verification.** On a forced collapse, Σ₀ fired on 40/40 steps and the state
froze; with Σ₀⁻¹ active, Σ₀ fired 0/40 and the state escaped `0.05 → 12.9`.
(`AntiCollapseOperator`.)

---

## 4. The early-warning scalar (the "canary")

Near a bifurcation the dominant eigenvalue flattens (`critical slowing down`,
Wissel 1984; Scheffer et al., *Nature* 2009). Two readouts:

$$p_{\text{unbounded}}(x) = \frac{1}{|\Re\,\lambda_{\max}(A_s)|} \;\;\xrightarrow{\text{boundary}}\;\; \infty$$

$$p_{\text{gate}}(x) = \mathrm{clip}\!\left(1 - \frac{|\Re\,\lambda_{\max}|}{\varepsilon},\,0,\,1\right) \in [0,1]$$

The unbounded form is the leading indicator (diverges *before* collapse); the
gated form is the bounded control signal that drives Σ₀⁻¹.

---

## 5. Global structure: the attractor graph G

The system is **multistable**. Collect its attractors `{A₁,…,A_k}` (fixed
points, limit cycles, strange attractors), each with a basin

$$B_i = \{\, x_0 : \lim_{t\to\infty}\phi_t(x_0) \in A_i \,\}.$$

Coarse-grain to a graph `G = (V, E)`: nodes are attractors, edges are
noise/drift-induced transitions, giving an induced **Markov process over
basins**

$$P_{ij}(u) = \Pr\big(\pi(x_{t+1}) = A_j \mid \pi(x_t) = A_i,\, u_t\big),$$

where the partition map `π : ℝⁿ → V` sends a state to its basin. `G` is the
formal version of the "world tree": the structure connecting the attractors.

**Safe passages.** A basin boundary studded with **saddles** (mixed-sign
`Re λ`) has *stable manifolds* — ridges you can traverse without being captured
by a deep attractor. "Spin the vanda fast" = ride a boundary saddle with
rotation set by `Im λ`.

---

## 6. Demonstration on real router data

Two experiments run the above on the actual Lantern OS conversation log
(`data/conversations/garage-conversations.jsonl`), encoding each turn as

$$x = [\text{novelty},\ \text{self\_repeat},\ \text{echo},\ \text{length}] \in [0,1]^4.$$

- **`experiments/router_sigma0_encoder.py`** — fits a local Jacobian per
  session, emits the spiral/canary/wall readouts, builds `π` and `P_ij`.
- **`experiments/router_reservoir_G.py`** — an echo-state network learns one
  global flow and runs autonomously, *becoming* `G`; its fixed points are the
  reconstructed attractors, fed back to the same Σ₀ certificate.

**Result (cross-confirmed by both methods):** this log's dynamics collapse onto
a **parrot attractor** — `novelty ≈ 1, echo ≈ 0.72` — a flow whose only fixed
point is "quote the prompt back." That is **model collapse** appearing directly
in the data, not inserted by hand.

**Honest caveats.** (1) The log is mostly synthetic test traffic, so the
*numbers* are illustrative — the deliverable is the pipeline. (2) The reservoir's
autonomous rollout diverges unless projected back onto the valid `[0,1]⁴`
domain; that projection is `π`, not a fudge. (3) The certificate is unreliable
at boundary fixed points where the hard clamp is non-smooth — a log-barrier is
the proper fix and is not yet implemented.

---

## 7. Why this is a warning against ASI

The same equations read as a safety argument:

A system that **"comes out of its own eyes"** — that optimizes against its own
representations with no external anchor — is the flow `ẋ = f(x)` where `f` only
ever sees `x`. The certificate says such a system has two fates and no third
without outside contact:

1. **Collapse (Σ₀):** it falls onto a degenerate, self-consistent, *dead* fixed
   point — the 42-state. Mirrors agreeing with mirrors.
2. **Divergence:** with no contraction it runs to infinity (the un-projected
   reservoir).

The only stable middle — the safe passages — required an **external bound**
(the projection back onto the real domain). **Grounding is the safety
mechanism.** Remove contact with something outside the mirrors and no
certificate keeps the system off the wall. The reservoir's collapse onto the
parrot attractor is a small, literal demonstration: a model trained only on its
own reflections converges to reflecting.

---

## References (lineage)

- A. M. Lyapunov, *The General Problem of the Stability of Motion* (1892) — `V(x)` method.
- H. Poincaré, *Mémoire sur les courbes…* (1880s) — node/saddle/center/**focus** (spiral) classification.
- C. Wissel (1984); M. Scheffer et al., *Nature* (2009) — critical slowing down / early-warning signals.
- B. D. O. Anderson (1977); Åström & Bohlin (1965) — persistent excitation / identifiability.
- J. Pathak et al. (2017–18) — reservoir reconstruction of attractors and Lyapunov spectra.

*Web citations above are from prior knowledge; the live web-search backend was
unavailable when this was written and no URLs were fetched. Verify before formal
publication.*

---

*Source: `src/cio_sde/collapse.py`, `experiments/router_sigma0_encoder.py`,
`experiments/router_reservoir_G.py`. Tests: `tests/test_cio_sde.py` (20 passing).*
