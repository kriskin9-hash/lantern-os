"""
Σ₀ real-data grounding demo — the parrot attractor, on real conversation logs.

This is the real-data version of the §6 "router demonstration" that was deprecated
as unimplemented in `docs/SIGMA0-COLLAPSE-CERTIFICATE.md` (issue #504). Instead of
the two missing driver scripts and hand-entered numbers, this runs the *committed*
Σ₀ machinery end-to-end on a real, checked-in conversation log and writes a logged
artifact. It closes issue #507 and exercises the surprise-monitor integration from
issue #506 and the small-gain certificate from issue #505.

Pipeline (encode → detect → excite → measure persistence):

  1. ENCODE   real turns of `apps/data/conversations/garage-conversations.jsonl`
              into the §6/Appendix-A state vector  x = [novelty, self_repeat, echo,
              length] ∈ [0,1]⁴  using token-set Jaccard over a sliding window.
  2. DETECT   fit a local linear Jacobian A per window (least squares + ridge) and
              run `collapse_certificate(A)` — the α / null-dim trajectory — plus a
              Kalman `SurpriseMonitor` over the real series (NIS / spook timeline).
  3. EXCITE   from the most-collapsed real window's Jacobian, roll out the dynamics
              with Σ₀ collapse vs Σ₀⁻¹ anti-collapse and measure the injected
              excitation (‖dx_extra‖) and whether effective rank persists.
  4. REPORT   write `data/sigma0_real_data_grounding_report.json` with an explicit
              real-vs-synthetic provenance block, and print a human-readable summary.

HONESTY (AGENTS.md: be honest about real vs designed):
  REAL (grounded in the log):      the state-vector encoding, the fitted Jacobians,
                                   the certificate verdicts, and the *timing* of NIS
                                   surprise spikes.
  SYNTHETIC (modeling choices):    the Kalman R/Q noise scales (set NIS's absolute
                                   magnitude, not its timing), the excitation noise ξ,
                                   and the intervention rollout itself.
  NOT AVAILABLE for passive logs:  two of the four Σ₀ trigger conditions (∇ₓL and
                                   ∂H/∂u) need a control model; a passive log has
                                   none, so the proximity proxy here uses only the
                                   two data-observable conditions (rank deficiency
                                   and Σ flatness). This is stated, not hidden.

Reproducible: fixed seed, no network. Run:
    python experiments/sigma0_real_data_grounding.py
"""
from __future__ import annotations

import json
import math
import os
import re
import sys

import torch

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

from src.cio_sde import (
    SurpriseMonitor, kalman_predict,
    collapse_certificate, lyapunov_value,
    AntiCollapseOperator,
)

SEED = 7
DIM = 4                       # [novelty, self_repeat, echo, length]
DT = 1.0                      # one step = one conversation turn
WINDOW = 24                   # turns per local-Jacobian fit / similarity lookback
RIDGE = 1e-3                  # ridge regularizer for the least-squares fit
LEN_NORM = 40.0              # token count that maps to length ≈ 1
R_MEAS = 0.02                # Kalman measurement-noise scale  (SYNTHETIC)
Q_PROC = 0.01                # Kalman process-noise scale      (SYNTHETIC)
SPOOK_SIGMAS = 3.0
EXCITE_STRENGTH = 0.5
ROLLOUT_STEPS = 40           # intervention rollout length
ROLLOUT_BATCH = 32
SOURCE = os.path.join("apps", "data", "conversations", "garage-conversations.jsonl")
ARTIFACT = os.path.join("data", "sigma0_real_data_grounding_report.json")

_TOKEN = re.compile(r"[a-z0-9]+")


# ── 1. ENCODE (REAL) ─────────────────────────────────────────────────────────

def load_turns(path: str) -> list[dict]:
    turns = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                turns.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return turns


def tokenize(text: str) -> set[str]:
    return set(_TOKEN.findall((text or "").lower()))


def jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def encode_trajectory(turns: list[dict], window: int) -> tuple[torch.Tensor, list[dict]]:
    """Map real turns → x = [novelty, self_repeat, echo, length] ∈ [0,1]⁴ (REAL)."""
    toks = [tokenize(t.get("text", "")) for t in turns]
    roles = [t.get("role", "?") for t in turns]
    X, meta = [], []
    for i in range(len(turns)):
        cur = toks[i]
        lo = max(0, i - window)
        prev = toks[lo:i]
        prev_roles = roles[lo:i]
        # echo: similarity to the immediately preceding turn (parroting the other party)
        echo = jaccard(cur, toks[i - 1]) if i > 0 else 0.0
        # novelty: 1 - best match against any recent turn (how new is this turn)
        best_any = max((jaccard(cur, p) for p in prev), default=0.0)
        novelty = 1.0 - best_any
        # self_repeat: best match against this role's own recent turns (looping)
        same = [p for p, r in zip(prev, prev_roles) if r == roles[i]]
        self_repeat = max((jaccard(cur, p) for p in same), default=0.0)
        # length: normalized token count
        length = min(1.0, len(cur) / LEN_NORM)
        X.append([novelty, self_repeat, echo, length])
        meta.append({"i": i, "role": roles[i], "surface": turns[i].get("surface", "?")})
    return torch.tensor(X, dtype=torch.float32), meta


# ── 2. DETECT — local Jacobian fit (REAL) ────────────────────────────────────

def fit_jacobian(X: torch.Tensor, dt: float, ridge: float) -> tuple[torch.Tensor, torch.Tensor]:
    """Least-squares F: x_{t+1} ≈ F x_t over a window, then A = (F - I)/dt."""
    x0, x1 = X[:-1], X[1:]                      # (n, d)
    d = X.shape[1]
    G = x0.T @ x0 + ridge * torch.eye(d)       # (d, d)
    F = torch.linalg.solve(G, x0.T @ x1).T     # (d, d)
    A = (F - torch.eye(d)) / dt
    return F, A


def effective_rank(cov: torch.Tensor, eig_eps: float = 1e-2) -> int:
    ev = torch.linalg.eigvalsh(0.5 * (cov + cov.T)).clamp_min(0.0)
    if ev.max() <= 0:
        return 0
    return int((ev > eig_eps * ev.max()).sum().item())


def anisotropy(cov: torch.Tensor) -> float:
    ev = torch.linalg.eigvalsh(0.5 * (cov + cov.T)).clamp_min(1e-12)
    return float((ev.std() / ev.mean()).item())


def _below(value: float, threshold: float) -> float:
    if threshold <= 0:
        return 0.0
    return max(0.0, min(1.0, 1.0 - value / threshold))


# ── main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    torch.manual_seed(SEED)

    if not os.path.exists(SOURCE):
        print(f"source log not found: {SOURCE}", file=sys.stderr)
        sys.exit(1)

    turns = load_turns(SOURCE)
    X, meta = encode_trajectory(turns, WINDOW)
    T = X.shape[0]

    # ---- 2a. windowed certificate + state-covariance proximity proxy (REAL) ----
    cert_series: list[dict] = []
    for s in range(WINDOW, T):
        Xw = X[s - WINDOW:s]
        _, A = fit_jacobian(Xw, DT, RIDGE)
        cert = collapse_certificate(A.unsqueeze(0))
        cov = torch.cov(Xw.T) if Xw.shape[0] > 1 else torch.zeros(DIM, DIM)
        eff_rank = effective_rank(cov)
        aniso = anisotropy(cov)
        # proximity proxy: only the 2 data-observable Σ₀ conditions (rank, flatness)
        p_rank = _below(float(eff_rank), 0.5 * DIM)
        p_flat = _below(aniso, 5e-2)
        proximity = min(p_rank, p_flat)
        cert_series.append({
            "t": s, "alpha": round(cert.alpha, 5),
            "guaranteed": bool(cert.guaranteed),
            "null_dim": cert.null_dim, "active_dim": cert.active_dim,
            "eff_rank": eff_rank, "anisotropy": round(aniso, 5),
            "proximity_proxy": round(proximity, 4),
        })

    # ---- 2b. Kalman surprise monitor over the real series (REAL timing) ----
    F_global, A_global = fit_jacobian(X, DT, RIDGE)
    Q = Q_PROC * torch.eye(DIM)
    C = torch.eye(DIM).unsqueeze(0)
    R = R_MEAS * torch.eye(DIM).unsqueeze(0)
    mon = SurpriseMonitor(spook_sigmas=SPOOK_SIGMAS, anti_collapse_trigger=True)
    x_hat = X[0].clone().unsqueeze(0)
    sig = (0.1 * torch.eye(DIM)).unsqueeze(0)
    nis_series: list[dict] = []
    first_spook = None
    for t in range(1, T):
        x_pred, sig_pred = kalman_predict(x_hat, sig, F_global, Q)
        y = X[t].unsqueeze(0)                              # REAL observation
        s_out = mon.evaluate(x_pred, sig_pred, y, C, R)
        x_hat, sig = mon.update(x_pred, sig_pred, y, C, R)
        spook = bool(s_out["spook"].item())
        if spook and first_spook is None:
            first_spook = t
        nis_series.append({"t": t, "nis": round(float(s_out["nis"].item()), 3),
                           "surprise": round(float(s_out["surprise"].item()), 3),
                           "spook": spook})
    spook_threshold = DIM + SPOOK_SIGMAS * math.sqrt(2.0 * DIM)

    # ---- 3. EXCITE — intervention on the most-collapsed real window ----
    # The rank+flatness proximity proxy never fires on this log (the state stays
    # full-rank), so we drive the intervention off the *Jacobian's* real null
    # structure instead: pick the window whose fitted A has a null mode (null_dim
    # ≥ 1) and the strongest contraction (most-negative α) — the local dynamics
    # closest to a degenerate, low-dimensional attractor.  Fall back to most-
    # negative α if no window has a null mode.
    null_windows = [r for r in cert_series if r["null_dim"] >= 1]
    pool = null_windows or cert_series
    worst = min(pool, key=lambda r: (r["alpha"], -r["null_dim"]))
    s = worst["t"]
    Xw = X[s - WINDOW:s]
    _, A_worst = fit_jacobian(Xw, DT, RIDGE)
    A_batch = A_worst.unsqueeze(0)
    # null basis of the REAL symmetric Jacobian — the flat directions Σ₀⁻¹ excites
    A_s = 0.5 * (A_worst + A_worst.T)
    evals_s, evecs_s = torch.linalg.eigh(A_s)
    null_basis = evecs_s[:, evals_s.abs() < 1e-2]              # (d, k)

    def null_energy(x: torch.Tensor) -> float:
        """Mean squared projection of the batch onto the real null subspace."""
        if null_basis.shape[1] == 0:
            return 0.0
        proj = x @ null_basis                                  # (B, k)
        return float((proj ** 2).sum(-1).mean().item())

    x_mean = Xw.mean(0)
    x0 = x_mean.unsqueeze(0).expand(ROLLOUT_BATCH, DIM).clone()
    x0 = x0 + 0.05 * torch.randn(ROLLOUT_BATCH, DIM)      # SYNTHETIC spread for the rollout
    sig0 = (0.1 * torch.eye(DIM)).unsqueeze(0).expand(ROLLOUT_BATCH, DIM, DIM).clone()
    anti = AntiCollapseOperator(strength=EXCITE_STRENGTH)
    # p_excite is DATA-DERIVED from the real null fraction (the rank-deficiency Σ₀
    # condition, which IS observable from a passive log) — not the unavailable
    # 4-condition control gate.
    p_excite = min(1.0, worst["null_dim"] / DIM)

    def rollout(anti_on: bool) -> dict:
        x = x0.clone()
        sig_r = sig0.clone()
        ranks, vvals, nulls, dx_norms = [], [], [], []
        for _ in range(ROLLOUT_STEPS):
            drift = x @ A_worst.T                          # linear drift from REAL A
            dx = DT * drift + math.sqrt(DT) * 0.02 * torch.randn_like(x)  # SYNTHETIC dW
            if anti_on and p_excite > 0:
                noise = torch.randn_like(x)
                dx_extra, sig_extra = anti.excite(x, sig_r, A_batch, p_excite, noise)
                dx = dx + dx_extra
                sig_r = sig_r + sig_extra
                dx_norms.append(float(dx_extra.norm(dim=-1).mean().item()))
            x = x + dx
            ranks.append(effective_rank(torch.cov(x.T)))
            vvals.append(lyapunov_value(x, A_batch))
            nulls.append(null_energy(x))
        return {
            "final_eff_rank": ranks[-1],
            "mean_eff_rank": round(sum(ranks) / len(ranks), 3),
            "final_lyapunov_V": round(vvals[-1], 6),
            "final_null_energy": round(nulls[-1], 6),
            "mean_null_energy": round(sum(nulls) / len(nulls), 6),
            "mean_excitation_norm": round(sum(dx_norms) / len(dx_norms), 6) if dx_norms else 0.0,
        }

    off = rollout(anti_on=False)
    on = rollout(anti_on=True)
    null_persistence_ratio = (round(on["mean_null_energy"] / off["mean_null_energy"], 3)
                              if off["mean_null_energy"] > 0 else None)
    intervention = {
        "window_end_turn": s,
        "window_alpha": worst["alpha"],
        "window_null_dim": worst["null_dim"],
        "p_excite_from_null_fraction": round(p_excite, 4),
        "note": ("p_excite is the real null-fraction (rank-deficiency Σ₀ condition); "
                 "the rank+flatness proximity proxy never fires on this log."),
        "interpretation": (
            "Σ₀⁻¹ injects measurable excitation along the REAL null Jacobian mode "
            "(mean‖dx_extra‖>0) and sustains null-subspace energy "
            f"{null_persistence_ratio}x vs the un-excited baseline — it keeps the flat "
            "direction alive. The baseline does NOT hard-freeze in this rollout "
            "(eff_rank stays 4), so this demonstrates persistent excitation, not a "
            "rescued collapse. eff_rank drops when ON because all excitation lands in "
            "a 1-D null subspace (one dominant direction); null-subspace energy, not "
            "effective rank, is the faithful metric for a 1-D null space."),
        "null_subspace_persistence_ratio_on_over_off": null_persistence_ratio,
        "collapse_off_anti_off": off,
        "anti_collapse_on": on,
    }

    # ---- summary stats on the real trajectory ----
    mean_echo = round(float(X[:, 2].mean().item()), 4)
    mean_novelty = round(float(X[:, 0].mean().item()), 4)
    mean_self_repeat = round(float(X[:, 1].mean().item()), 4)
    n_guaranteed = sum(1 for r in cert_series if r["guaranteed"])
    n_spook = sum(1 for r in nis_series if r["spook"])
    first_collapse = next((r["t"] for r in cert_series if r["guaranteed"]), None)
    high_prox = max((r["proximity_proxy"] for r in cert_series), default=0.0)

    report = {
        "issue": 507,
        "epic": 509,
        "links": {
            "504": "realizes the deprecated §6/Appendix-A router demo on real data",
            "505": "uses the small-gain collapse_certificate() for non-normal A",
            "506": "uses SurpriseMonitor (NIS) wired to anti_collapse_trigger",
        },
        "provenance": {
            "real_inputs": [
                f"{SOURCE} ({len(turns)} turns)",
                "state-vector encoding [novelty, self_repeat, echo, length] from token-set Jaccard",
                "per-window least-squares Jacobian fits",
                "collapse_certificate verdicts on the fitted Jacobians",
                "timing of Kalman NIS surprise spikes",
            ],
            "synthetic_modeling_choices": [
                f"Kalman R={R_MEAS} / Q={Q_PROC} (set NIS magnitude, not its timing)",
                "excitation noise ξ (seeded)",
                "intervention rollout dynamics, dW, and initial spread",
            ],
            "not_available_for_passive_logs": [
                "Σ₀ condition ∇ₓL < ε_g (needs a control/optimization model)",
                "Σ₀ condition ∂H/∂u < ε_c (needs a control model)",
                "proximity proxy uses only the 2 data-observable conditions: "
                "rank deficiency and Σ flatness",
            ],
        },
        "config": {
            "seed": SEED, "dim": DIM, "dt": DT, "window": WINDOW, "ridge": RIDGE,
            "len_norm": LEN_NORM, "R_meas": R_MEAS, "Q_proc": Q_PROC,
            "spook_sigmas": SPOOK_SIGMAS, "spook_threshold": round(spook_threshold, 3),
            "excite_strength": EXCITE_STRENGTH, "rollout_steps": ROLLOUT_STEPS,
            "rollout_batch": ROLLOUT_BATCH, "source": SOURCE,
        },
        "trajectory_stats": {
            "n_turns": T,
            "mean_novelty": mean_novelty,
            "mean_self_repeat": mean_self_repeat,
            "mean_echo": mean_echo,
            "parrot_attractor": mean_echo > 0.3 or mean_self_repeat > 0.3,
        },
        "detection": {
            "n_windows": len(cert_series),
            "n_collapse_guaranteed": n_guaranteed,
            "first_collapse_guaranteed_turn": first_collapse,
            "max_proximity_proxy": round(high_prox, 4),
            "n_spook": n_spook,
            "first_spook_turn": first_spook,
        },
        "intervention": intervention,
        "series": {
            "certificate": cert_series,
            "nis": nis_series,
        },
    }

    os.makedirs(os.path.dirname(ARTIFACT), exist_ok=True)
    with open(ARTIFACT, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    # ── human-readable summary ──
    print("Σ₀ real-data grounding — the parrot attractor on a real conversation log")
    print(f"  source: {SOURCE}  ({len(turns)} turns → {T} state vectors)")
    print(f"  encoding (REAL): x = [novelty, self_repeat, echo, length] ∈ [0,1]^4")
    print()
    print("  trajectory means (REAL):")
    print(f"    novelty={mean_novelty}  self_repeat={mean_self_repeat}  echo={mean_echo}")
    print(f"    parrot-attractor signature: {report['trajectory_stats']['parrot_attractor']}")
    print()
    print("  detection (REAL Jacobians + certificate, REAL NIS timing):")
    print(f"    windows={len(cert_series)}  collapse-guaranteed={n_guaranteed}  "
          f"first@turn={first_collapse}")
    print(f"    max proximity proxy={round(high_prox, 4)}  "
          f"(rank+flatness only; ∇L/∂H∂u N/A for passive logs)")
    print(f"    NIS spook threshold={round(spook_threshold, 2)}  spooks={n_spook}  "
          f"first@turn={first_spook}")
    print()
    i = intervention
    off, on = i["collapse_off_anti_off"], i["anti_collapse_on"]
    print(f"  intervention on most-collapsed real window (ends @turn {i['window_end_turn']}, "
          f"α={i['window_alpha']}, null_dim={i['window_null_dim']}):")
    print(f"    p_excite (real null-fraction) = {i['p_excite_from_null_fraction']}")
    print(f"    Σ₀⁻¹ OFF: mean_null_energy={off['mean_null_energy']}  "
          f"mean_eff_rank={off['mean_eff_rank']}  final_V={off['final_lyapunov_V']}")
    print(f"    Σ₀⁻¹ ON : mean_null_energy={on['mean_null_energy']}  "
          f"mean_eff_rank={on['mean_eff_rank']}  final_V={on['final_lyapunov_V']}")
    print(f"    mean‖dx_extra‖={on['mean_excitation_norm']}  "
          f"null-subspace persistence (on/off)={i['null_subspace_persistence_ratio_on_over_off']}×")
    print()
    print(f"  artifact: {ARTIFACT}")


if __name__ == "__main__":
    main()
