"""Machine-check — the contraction half of [#768]: Theorem 1's spectral-dichotomy
extension to NON-NORMAL A.

Theorem 1 (collapse onto the manifold) was proven only for normal A, via the orthogonal
A_s split, which fails for non-normal A (the §1 cross-term P_M A P_N ≠ 0). The fix is to
split by A's OWN spectrum (the oblique Riesz projector), which is A-invariant, so the
cross-term is identically zero. This script validates the shipped certificate
(`src.cio_sde.collapse.dichotomy_certificate`) over a random ensemble of genuinely
non-normal A, by INDEPENDENT simulation, on the three load-bearing claims:

  (a) INVARIANCE — Π_M (Riesz projector onto {Re λ < −δ}) commutes with A; equivalently
      the active subspace is A-invariant, so the certificate's `invariance_residual`
      ‖(I−BBᵀ)A B‖ ≈ 0.
  (b) ACTIVE DECAY (bounded transient) — evolved in an ORTHONORMAL basis of the active
      subspace via the REDUCED dynamics c(t)=e^{tAᴹ}c₀ (so the divergent slow modes can
      never contaminate it), ‖c(t)‖ ≤ √cond(P)·e^{−t/(2λ_max(P))}·‖c₀‖ at every sampled t
      — the certified envelope (transient_bound, active_decay_rate). The active modes
      ALWAYS die, within the certified overshoot, regardless of the slow fate.
  (c) DICHOTOMY (no third fate) — the slow block is evolved by its OWN reduced dynamics
      d(t)=e^{tAᴺ}d₀; the observed long-time fate matches sign(β), β=slow_abscissa:
      β>tol ⇒ DIVERGE, β<−tol ⇒ COLLAPSE, |β|≤tol ⇒ MARGINAL (bounded onto center). In
      every trial the active part decays AND the fate matches the certificate — there is
      no run where the system neither collapses nor diverges-while-active-persists.

The earlier version of this script evolved the FULL propagator e^{tA}Π_M x₀ and used
−max Re λ as the rate; that amplified projector roundoff in the unstable direction and
used an envelope that is not valid at finite t. Both are fixed here (reduced dynamics +
the Lyapunov envelope), per docs/SIGMA0-T1-NONNORMAL-DICHOTOMY.md §3.1.

Run: python experiments/prove_t1_nonnormal_dichotomy.py
"""
from __future__ import annotations
import sys
from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

import numpy as np
from scipy.linalg import expm
import torch

from src.cio_sde.collapse import dichotomy_certificate

DELTA = 0.25          # split threshold: active = {Re λ < −δ}, slow = {Re λ ≥ −δ}
GAP = 0.1             # keep the spectrum clear of the split line so Π_M stays well-conditioned
TOL_INVARIANCE = 1e-8
TOL_FATE = 1e-3


def random_nonnormal(n, rng):
    """Real non-normal A with a random spectrum (real eigenvalues + complex pairs), no
    eigenvalue within GAP of the split line −δ, conjugated by an ill-conditioned real S."""
    re_parts, blocks, k = [], [], 0
    while k < n:
        r = rng.uniform(-3.0, 1.0)
        if abs(r + DELTA) < GAP:                 # avoid the [−δ−GAP, −δ+GAP] band
            continue
        if k <= n - 2 and rng.random() < 0.5:
            w = rng.uniform(0.3, 2.0)            # complex pair r ± wi
            blocks.append(np.array([[r, w], [-w, r]], float)); re_parts += [r, r]; k += 2
        else:
            blocks.append(np.array([[r]], float)); re_parts.append(r); k += 1
    Lam = np.zeros((n, n)); i = 0
    for B in blocks:
        b = B.shape[0]; Lam[i:i + b, i:i + b] = B; i += b
    cond = rng.uniform(5.0, 300.0)
    U, _, _ = np.linalg.svd(rng.standard_normal((n, n)))
    _, _, Wt = np.linalg.svd(rng.standard_normal((n, n)))
    S = U @ np.diag(np.linspace(1.0, cond, n)) @ Wt
    return S @ Lam @ np.linalg.inv(S)


def invariant_bases(A, delta):
    """Orthonormal bases (B active, C slow) of A's spectral-split invariant subspaces,
    the oblique projector Π_M, and the reduced generators Aᴹ=BᵀAB, Aᴺ=CᵀAC. Evolving in
    B/C stays inside each invariant subspace — no cross-contamination."""
    w, V = np.linalg.eig(A)
    mask = (w.real < -delta).astype(complex)
    Pi_M = np.real_if_close(V @ np.diag(mask) @ np.linalg.inv(V), tol=1000).real
    n = A.shape[0]
    U, s, _ = np.linalg.svd(Pi_M); r = int((s > 1e-9).sum())
    B = U[:, :r] if r > 0 else np.zeros((n, 0))
    Uc, sc, _ = np.linalg.svd(np.eye(n) - Pi_M); rc = int((sc > 1e-9).sum())
    C = Uc[:, :rc] if rc > 0 else np.zeros((n, 0))
    return B, C, Pi_M, (B.T @ A @ B), (C.T @ A @ C)


def sweep(n_trials=600):
    rng = np.random.default_rng(20260626)
    dims = [4, 5, 6, 8]
    ts = np.array([0.5, 1, 2, 4, 8, 16, 32.0])

    invariance_fail = envelope_violations = active_not_decayed = fate_mismatch = 0
    checked = 0
    worst_resid = worst_env_ratio = 0.0

    for t in range(n_trials):
        n = dims[t % len(dims)]
        A = random_nonnormal(n, rng)
        # float64 so the certified envelope is computed on the exact A the simulation uses
        cert = dichotomy_certificate(torch.tensor(A, dtype=torch.float64), delta=DELTA)
        B, C, Pi_M, A_M, A_N = invariant_bases(A, DELTA)
        x0 = rng.standard_normal(n)

        # (a) invariance — certificate residual ‖(I−BBᵀ)A B‖ ≈ 0
        worst_resid = max(worst_resid, cert.invariance_residual)
        if cert.invariance_residual > TOL_INVARIANCE:
            invariance_fail += 1

        # (b) active decay within the certified envelope √cond(P)·e^{−t/(2λmax(P))},
        #     evolved by the REDUCED active dynamics (no slow contamination)
        if B.shape[1] > 0:
            c0 = B.T @ (Pi_M @ x0)                 # active component, in the ON basis
            a0 = np.linalg.norm(c0)
            if a0 > 1e-9:
                for tt in ts:
                    ct = np.linalg.norm(expm(A_M * tt) @ c0)
                    bound = cert.transient_bound * np.exp(-cert.active_decay_rate * tt) * a0
                    if ct > bound * (1 + 1e-6):
                        envelope_violations += 1
                    worst_env_ratio = max(worst_env_ratio, ct / (bound + 1e-300))
                if np.linalg.norm(expm(A_M * 200.0) @ c0) > 1e-4 * a0:
                    active_not_decayed += 1

        # (c) dichotomy — evolve the slow block by its OWN reduced dynamics and estimate
        #     its late-time exponential rate; it must land in the same sign-bucket as the
        #     certificate's β (the claim: fate = sign β), robust to β's magnitude. Using
        #     the rate's SIGN avoids the fixed-threshold fragility of near-marginal cases.
        def bucket(x):
            return "DIVERGE" if x > TOL_FATE else ("COLLAPSE" if x < -TOL_FATE else "MARGINAL")
        if C.shape[1] > 0:
            d0 = C.T @ (np.eye(n) - Pi_M) @ x0
            if np.linalg.norm(d0) > 1e-9:
                t1, t2 = 100.0, 200.0              # late enough to be asymptotic in β
                d1 = np.linalg.norm(expm(A_N * t1) @ d0)
                d2 = np.linalg.norm(expm(A_N * t2) @ d0)
                emp_rate = (np.log(d2) - np.log(d1)) / (t2 - t1) if (d1 > 0 and d2 > 0) else -np.inf
                if bucket(emp_rate) != bucket(cert.slow_abscissa):
                    fate_mismatch += 1
        else:
            # no slow block ⇒ whole system Hurwitz ⇒ certificate must say COLLAPSE
            if cert.fate != "COLLAPSE":
                fate_mismatch += 1
        checked += 1

    print(f"[sweep] checked {checked} random non-normal A (d∈{dims}, δ={DELTA})")
    print(f"(a) invariance    residual > {TOL_INVARIANCE:g} : {invariance_fail}/{checked}  "
          f"(worst ‖(I−BBᵀ)AB‖ = {worst_resid:.2e})")
    print(f"(b) active decay  certified-envelope violations : {envelope_violations}  | "
          f"active-not-decayed : {active_not_decayed}  (worst obs/bound ratio {worst_env_ratio:.3f})")
    print(f"(c) dichotomy     fate ≠ sign(β) mismatches : {fate_mismatch}  (no third fate ⇒ 0)")
    ok = (invariance_fail == 0 and envelope_violations == 0 and active_not_decayed == 0
          and fate_mismatch == 0 and checked > 400 and worst_env_ratio <= 1.0 + 1e-6)
    return ok


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    print("Theorem 1 — non-normal spectral-dichotomy machine-check (#768 contraction half)\n")
    ok = sweep()
    print(f"\nT1 NON-NORMAL DICHOTOMY {'VERIFIED' if ok else 'FAILED'} — in A's own spectral "
          "split the cross-term vanishes; active modes decay within the certified Lyapunov "
          "envelope; the fate is exactly sign(slow abscissa). No third fate.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
