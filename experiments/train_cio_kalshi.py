"""
Train the CIO dynamics on historical Kalshi odds trajectories (#392).

Task: one-step-ahead prediction of the de-vigged YES probability.
  state  p_t = yes_ask / (yes_ask + no_ask)   in [0,1]
  model  dp ~ N( f(p)·dt , g(p)²·dt )          (the CIO SDE step)
  loss   Gaussian negative log-likelihood       (= free-energy reconstruction term)

We fit src.cio_sde.engine.Dynamics (drift f + diffusion g) — the same module the
runtime uses — and hold out a set of UNSEEN tickers for validation. The honest
bar is the persistence baseline (predict dp = 0); a model that can't beat it on
held-out tickers has learned nothing useful.

Run:  PYTHONIOENCODING=utf-8 python experiments/train_cio_kalshi.py
"""

import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import torch

from src.cio_sde.engine import Dynamics

REPO = Path(__file__).resolve().parents[1]
SNAPSHOTS = REPO / "data" / "kalshi" / "price-snapshots.jsonl"
OUT_MODEL = REPO / "data" / "kalshi" / "cio-model.pt"
OUT_REPORT = REPO / "data" / "kalshi" / "cio-train-report.json"

DT = 1.0           # one collector round per step
MIN_POINTS = 6     # drop tickers with too few snapshots
SEED = 0


def load_series():
    """ticker -> chronological list of de-vigged YES probabilities."""
    rows = {}
    with open(SNAPSHOTS, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            t = r.get("ticker")
            if not t:
                continue
            ya, na = float(r.get("yes_ask") or 0), float(r.get("no_ask") or 0)
            if ya + na <= 0:
                continue
            rows.setdefault(t, []).append((r.get("ts", ""), ya / (ya + na)))
    series = {}
    for t, pts in rows.items():
        pts.sort(key=lambda x: x[0])
        ps = [p for _, p in pts]
        if len(ps) >= MIN_POINTS:
            series[t] = ps
    return series


def build_transitions(series, tickers):
    """(p_t, dp) pairs for the given tickers."""
    P, DP = [], []
    for t in tickers:
        ps = series[t]
        for i in range(len(ps) - 1):
            P.append([ps[i]])
            DP.append([ps[i + 1] - ps[i]])
    return torch.tensor(P), torch.tensor(DP)


def gaussian_nll(dp, mu, sigma):
    var = sigma ** 2
    return (0.5 * ((dp - mu) ** 2 / var) + torch.log(sigma)).mean()


def rmse(a, b):
    return float(torch.sqrt(((a - b) ** 2).mean()).item())


def main():
    torch.manual_seed(SEED)
    series = load_series()
    tickers = sorted(series)
    if len(tickers) < 10:
        print(f"Not enough tickers with >= {MIN_POINTS} points: {len(tickers)}")
        return

    # split by TICKER so validation paths are genuinely unseen
    g = torch.Generator().manual_seed(SEED)
    perm = torch.randperm(len(tickers), generator=g).tolist()
    n_val = max(1, len(tickers) // 5)
    val_t = [tickers[i] for i in perm[:n_val]]
    train_t = [tickers[i] for i in perm[n_val:]]

    Ptr, DPtr = build_transitions(series, train_t)
    Pva, DPva = build_transitions(series, val_t)

    depth = sum(len(series[t]) for t in tickers) / len(tickers)
    print(f"tickers={len(tickers)} (train {len(train_t)} / val {len(val_t)})  "
          f"avg depth={depth:.1f}  transitions: train {len(Ptr)} / val {len(Pva)}")

    # CIO dynamics: 1-D state, control unused (zeros)
    model = Dynamics(dim=1, ctrl_dim=1, hidden=16)
    u_tr = torch.zeros(len(Ptr), 1)
    u_va = torch.zeros(len(Pva), 1)
    opt = torch.optim.Adam(model.parameters(), lr=5e-3)

    def predict(P, U):
        mu = model.drift(P, U) * DT
        sigma = (model.diffusion(P) * math.sqrt(DT)).clamp_min(1e-4)
        return mu, sigma

    best_val = math.inf
    best_state = None
    # Dynamics is Linear+SiLU only (no dropout/batchnorm), so train/eval modes
    # are no-ops; torch.no_grad() is what matters for the held-out passes.
    for epoch in range(400):
        opt.zero_grad()
        mu, sigma = predict(Ptr, u_tr)
        loss = gaussian_nll(DPtr, mu, sigma)
        loss.backward()
        opt.step()
        if epoch % 50 == 0 or epoch == 399:
            with torch.no_grad():
                vmu, vsig = predict(Pva, u_va)
                vnll = gaussian_nll(DPva, vmu, vsig).item()
                vrmse = rmse(vmu, DPva)
            if vnll < best_val:
                best_val = vnll
                best_state = {k: v.clone() for k, v in model.state_dict().items()}
            print(f"  epoch {epoch:3d}  train_nll {loss.item():+.4f}  "
                  f"val_nll {vnll:+.4f}  val_rmse {vrmse:.5f}")

    if best_state:
        model.load_state_dict(best_state)

    # ── honest evaluation vs persistence baseline ────────────────────────────
    with torch.no_grad():
        vmu, vsig = predict(Pva, u_va)
        model_rmse = rmse(vmu, DPva)
        base_rmse = rmse(torch.zeros_like(DPva), DPva)   # persistence: dp = 0
        # learned drift shape (mean-reversion vs momentum)
        grid = torch.tensor([[0.2], [0.35], [0.5], [0.65], [0.8]])
        drift_grid = (model.drift(grid, torch.zeros(5, 1)) * DT).squeeze(-1).tolist()
        diff_grid = model.diffusion(grid).squeeze(-1).tolist()

    improve = (base_rmse - model_rmse) / base_rmse * 100 if base_rmse else 0.0
    verdict = ("BEATS persistence" if model_rmse < base_rmse * 0.999
               else "no better than persistence")

    print("\n=== held-out result ===")
    print(f"  persistence RMSE : {base_rmse:.5f}")
    print(f"  CIO model   RMSE : {model_rmse:.5f}   ({improve:+.1f}% vs baseline)")
    print(f"  verdict          : {verdict}")
    print(f"  learned drift @ p=[.2 .35 .5 .65 .8]: "
          f"{[round(x, 5) for x in drift_grid]}")
    print(f"  learned vol   @ same p             : "
          f"{[round(x, 4) for x in diff_grid]}")
    mr = "mean-reverting" if drift_grid[0] > 0 and drift_grid[-1] < 0 else "no clear mean-reversion"
    print(f"  drift signature  : {mr}")

    report = {
        "tickers": len(tickers), "train_tickers": len(train_t), "val_tickers": len(val_t),
        "avg_depth": round(depth, 2),
        "train_transitions": len(Ptr), "val_transitions": len(Pva),
        "persistence_rmse": round(base_rmse, 6),
        "model_rmse": round(model_rmse, 6),
        "improvement_pct": round(improve, 2),
        "verdict": verdict,
        "drift_grid": {str(round(x.item(), 2)): round(d, 6) for x, d in zip(grid, drift_grid)},
        "vol_grid": {str(round(x.item(), 2)): round(v, 6) for x, v in zip(grid, diff_grid)},
    }
    OUT_REPORT.write_text(json.dumps(report, indent=2))
    torch.save(model.state_dict(), OUT_MODEL)
    print(f"\nsaved model  -> {OUT_MODEL}")
    print(f"saved report -> {OUT_REPORT}")


if __name__ == "__main__":
    main()
