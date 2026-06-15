"""
router_reservoir_G.py
======================
Trains an echo-state network (reservoir) on the Σ₀ state-vector stream produced
by `router_sigma0_encoder.py`, fitting a linear readout that reconstructs the
next state vector. This is the in-repo stand-in for the global attractor flow
`G` referenced in §6 of docs/SIGMA0-COLLAPSE-CERTIFICATE.md.

Pipeline:
  data/sigma0/router-encoder-output.jsonl  (states x_t ∈ [0,1]⁴)
        │
        ▼  drive a fixed random reservoir (size 50, spectral radius 0.9)
  reservoir states r_t ∈ R^50
        │
        ▼  ridge-regression readout  W_out : r_t → x_{t+1}
  one-step reconstruction  x̂_{t+1}
        │
        ▼  autonomous rollout (feed x̂ back) → does it collapse?

Reports:
  - one-step reconstruction MSE (train / held-out)
  - autonomous-rollout fixed point (the "parrot attractor" candidate)
  - approximate attractor (correlation) dimension of the reservoir trajectory

Outputs:
  data/sigma0/reservoir-G-output.jsonl  — per-step reconstruction + rollout tail

Run from repo root (after router_sigma0_encoder.py):
  python experiments/router_reservoir_G.py
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import List, Optional

import numpy as np

# ── paths ─────────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parent.parent
SIGMA0_DIR = REPO_ROOT / "data" / "sigma0"
IN_FILE = SIGMA0_DIR / "router-encoder-output.jsonl"
OUT_FILE = SIGMA0_DIR / "reservoir-G-output.jsonl"

# ── reservoir hyper-parameters ──────────────────────────────────────────────────

RESERVOIR_SIZE = 50
SPECTRAL_RADIUS = 0.9
LEAK = 0.3
INPUT_SCALE = 0.5
RIDGE = 1e-4
SEED = 42
WASHOUT = 20          # discard initial transient before fitting
ROLLOUT_STEPS = 200   # autonomous rollout to probe the attractor


def load_states() -> Optional[np.ndarray]:
    """Load the [novelty, self_repeat, echo, length] stream from the encoder."""
    if not IN_FILE.exists():
        return None
    states = []
    with open(IN_FILE, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            sv = obj.get("state")
            if sv and len(sv) == 4:
                states.append(sv)
    if not states:
        return None
    return np.asarray(states, dtype=float)


def build_reservoir(n_in: int, rng: np.random.Generator):
    """Fixed random reservoir scaled to the target spectral radius."""
    W = rng.uniform(-1.0, 1.0, size=(RESERVOIR_SIZE, RESERVOIR_SIZE))
    # sparsify (~10% connectivity) for richer dynamics
    mask = rng.uniform(size=W.shape) < 0.1
    W *= mask
    eigs = np.linalg.eigvals(W)
    rho = float(np.max(np.abs(eigs)))
    if rho > 0:
        W *= SPECTRAL_RADIUS / rho
    W_in = rng.uniform(-1.0, 1.0, size=(RESERVOIR_SIZE, n_in)) * INPUT_SCALE
    return W, W_in


def drive(W: np.ndarray, W_in: np.ndarray, inputs: np.ndarray) -> np.ndarray:
    """Run the reservoir over an input sequence; return collected states."""
    r = np.zeros(RESERVOIR_SIZE)
    out = np.zeros((len(inputs), RESERVOIR_SIZE))
    for t, u in enumerate(inputs):
        pre = W @ r + W_in @ u
        r = (1 - LEAK) * r + LEAK * np.tanh(pre)
        out[t] = r
    return out


def fit_readout(R: np.ndarray, targets: np.ndarray) -> np.ndarray:
    """Ridge regression  W_out : r → x_next."""
    n = R.shape[1]
    A = R.T @ R + RIDGE * np.eye(n)
    B = R.T @ targets
    return np.linalg.solve(A, B)   # (RESERVOIR_SIZE, n_out)


def correlation_dimension(traj: np.ndarray, n_pairs: int = 5000,
                          rng: Optional[np.random.Generator] = None) -> float:
    """
    Grassberger–Procaccia correlation-dimension estimate from pairwise
    distances of the reservoir trajectory. Coarse but committed-and-reproducible.
    """
    if rng is None:
        rng = np.random.default_rng(SEED)
    m = len(traj)
    if m < 50:
        return float("nan")
    i = rng.integers(0, m, size=n_pairs)
    j = rng.integers(0, m, size=n_pairs)
    keep = i != j
    d = np.linalg.norm(traj[i[keep]] - traj[j[keep]], axis=1)
    d = d[d > 0]
    if len(d) < 10:
        return float("nan")
    # slope of log C(r) vs log r over the central range
    lo, hi = np.percentile(d, [10, 90])
    radii = np.logspace(np.log10(lo), np.log10(hi), 12)
    logc, logr = [], []
    for rad in radii:
        c = float(np.mean(d < rad))
        if c > 0:
            logc.append(math.log(c))
            logr.append(math.log(rad))
    if len(logc) < 3:
        return float("nan")
    slope = float(np.polyfit(logr, logc, 1)[0])
    return slope


def main() -> None:
    SIGMA0_DIR.mkdir(parents=True, exist_ok=True)

    states = load_states()
    if states is None:
        print(f"[router_reservoir_G] No encoder output at {IN_FILE}.")
        print("  Run:  python experiments/router_sigma0_encoder.py")
        sys.exit(1)

    n = len(states)
    if n < WASHOUT + 30:
        print(f"[router_reservoir_G] Only {n} states — too few for a stable fit.")
        sys.exit(1)

    print(f"[router_reservoir_G] Loaded {n} state vectors from {IN_FILE.name}")

    rng = np.random.default_rng(SEED)
    W, W_in = build_reservoir(states.shape[1], rng)

    # Drive reservoir; align r_t → x_{t+1}
    R = drive(W, W_in, states)
    R_use = R[WASHOUT:-1]          # reservoir state at t
    X_next = states[WASHOUT + 1:]  # target x_{t+1}

    # train / held-out split (80/20)
    split = int(len(R_use) * 0.8)
    W_out = fit_readout(R_use[:split], X_next[:split])

    pred_train = R_use[:split] @ W_out
    pred_test = R_use[split:] @ W_out
    mse_train = float(np.mean((pred_train - X_next[:split]) ** 2))
    mse_test = float(np.mean((pred_test - X_next[split:]) ** 2))

    # Autonomous rollout: feed prediction back as next input
    r = R[-1].copy()
    u = states[-1].copy()
    rollout = []
    for _ in range(ROLLOUT_STEPS):
        pre = W @ r + W_in @ u
        r = (1 - LEAK) * r + LEAK * np.tanh(pre)
        u = np.clip(r @ W_out, 0.0, 1.0)   # project back onto [0,1]⁴ (= π)
        rollout.append(u.tolist())
    rollout_arr = np.asarray(rollout)
    fixed_point = rollout_arr[-50:].mean(axis=0)   # attractor estimate

    corr_dim = correlation_dimension(R[WASHOUT:], rng=rng)

    # Write per-step output (one-step recon over held-out + rollout tail)
    with open(OUT_FILE, "w", encoding="utf-8") as fh:
        for t in range(len(pred_test)):
            fh.write(json.dumps({
                "kind": "recon",
                "idx": split + t,
                "target": X_next[split + t].tolist(),
                "pred": pred_test[t].tolist(),
            }) + "\n")
        for k, u in enumerate(rollout):
            fh.write(json.dumps({"kind": "rollout", "step": k, "state": u}) + "\n")

    labels = ["novelty", "self_repeat", "echo", "length"]
    print(f"\n=== router_reservoir_G summary ===")
    print(f"  states                 : {n}")
    print(f"  reservoir size         : {RESERVOIR_SIZE}  (spectral radius {SPECTRAL_RADIUS})")
    print(f"  one-step MSE (train)   : {mse_train:.5f}")
    print(f"  one-step MSE (held-out): {mse_test:.5f}")
    print(f"  correlation dimension  : {corr_dim:.3f}")
    print(f"  autonomous fixed point :")
    for lab, val in zip(labels, fixed_point):
        print(f"      {lab:<12} = {val:.3f}")
    print(f"  output                 : {OUT_FILE}")


if __name__ == "__main__":
    main()
