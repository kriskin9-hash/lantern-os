"""
Σ₀ᴿ on a REAL log — "put the smoke back in a log," measured.

The synthetic version (experiments/sigma0_reconstruction.py) proves the
reconstruction operator works on a made-up world. This runs the same machine on
a real, committed conversation log and measures the rate–distortion floor on
real trajectory structure — the honest, data-grounded version of the
"entropy reversal" / "universe on a flash drive" claim, and a direct probe of
whitepaper prediction P5.

Pipeline (embed → fit → burn → seed → rebuild → measure):

  1. EMBED  every turn of apps/data/conversations/garage-conversations.jsonl into
            a d-dim hashed token-bag vector (REAL content; the bucket count is a
            DESIGNED knob).
  2. FIT    a global drift Jacobian A from the trajectory's one-step transitions
            (least squares + ridge), and certify contraction (collapse_certificate).
  3. BURN   collapse the trajectory onto A's null manifold — the active-mode
            structure is the "smoke."
  4. SEED   keep the top-k active-mode coefficients (the "speck of dust").
  5. REBUILD regrow with Σ₀ᴿ from (burnt state + seed), and compare against random
            re-excitation of equal energy (no record).
  6. MEASURE the rate–distortion curve, its floor, the smallest speck that hits a
            target fidelity, and the effective dimension of the real trajectory.

HONESTY (real vs designed):
  REAL     : the turns, the hashed embedding values, the fitted Jacobian A, the
             certificate verdict, and every distortion number.
  DESIGNED : the embedding dimension / hashing scheme, the ridge constant, and the
             target-fidelity threshold.
  NOT      : this reconstructs the EMBEDDED trajectory, not the original tokens —
   CLAIMED   it is lossy compression of dynamical structure, not text recovery,
             and the floor is exactly where information theory bites.

Reproducible: fixed seed, no network. Run:
    python experiments/sigma0_smoke_on_real_log.py
"""
from __future__ import annotations

import json
import os
import re
import sys
import zlib

import torch

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

from src.cio_sde import ReconstructionOperator, collapse_certificate, lyapunov_value

SEED = 7
DIM = 24                 # embedding dimension (DESIGNED)
RIDGE = 1e-2             # least-squares regularizer (DESIGNED)
EPS = 1e-2               # |λ| below this ⇒ null mode
TARGET_FIDELITY = 0.10   # "within 10% of the structure" defines the smallest speck
SOURCE = os.path.join("apps", "data", "conversations", "garage-conversations.jsonl")
ARTIFACT = os.path.join("data", "sigma0_smoke_on_real_log_report.json")

_TOKEN = re.compile(r"[a-z0-9]+")


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


def embed(turns: list[dict], dim: int) -> torch.Tensor:
    """Hashed token-bag embedding, sqrt-tf weighted, L2-normalized (REAL content)."""
    X = torch.zeros(len(turns), dim)
    for i, t in enumerate(turns):
        toks = _TOKEN.findall((t.get("text", "") or "").lower())
        if not toks:
            continue
        for tok in toks:
            # crc32 is a deterministic hash (builtin hash() is per-process random)
            X[i, zlib.crc32(tok.encode("utf-8")) % dim] += 1.0
        X[i] = X[i].sqrt()                          # sqrt-tf damps frequent tokens
        n = X[i].norm()
        if n > 0:
            X[i] = X[i] / n
    return X


def fit_jacobian(X: torch.Tensor, ridge: float) -> torch.Tensor:
    """Least-squares one-step map F: x_{t+1} ≈ F x_t, then A = F − I."""
    x0, x1 = X[:-1], X[1:]
    d = X.shape[1]
    G = x0.T @ x0 + ridge * torch.eye(d)
    F = torch.linalg.solve(G, x0.T @ x1).T
    return F - torch.eye(d)


def main() -> None:
    torch.manual_seed(SEED)
    if not os.path.exists(SOURCE):
        print(f"source log not found: {SOURCE}", file=sys.stderr)
        sys.exit(1)

    turns = load_turns(SOURCE)
    X = embed(turns, DIM)                            # (T, d) REAL embedded trajectory
    A = fit_jacobian(X, RIDGE)                       # (d, d) REAL fitted drift

    op = ReconstructionOperator(eig_eps=EPS)
    cert = collapse_certificate(A.unsqueeze(0), eig_eps=EPS)
    active_dim = int(op._active_basis(A).shape[1])
    null_dim = DIM - active_dim

    pre = lyapunov_value(X, A.unsqueeze(0), eig_eps=EPS)
    x_burnt = op.collapse(X, A)
    post = lyapunov_value(x_burnt, A.unsqueeze(0), eig_eps=EPS)

    burnt_norm = (X - x_burnt).norm(dim=-1)          # ‖active structure‖ per turn

    def distortion(x_hat) -> float:
        # 1.0 = fully burnt, 0.0 = perfect reconstruction (structure units)
        return float(((x_hat - X).norm(dim=-1) / (burnt_norm + 1e-12)).mean())

    rng = torch.Generator().manual_seed(SEED + 1)
    V = op._active_basis(A)
    rows = []
    smallest_speck = None
    for k in range(0, active_dim + 1):
        s = op.seed(X, A, k)
        d_ref = distortion(op.reconstruct(x_burnt, s))

        energy = ((s["coeffs"] ** 2).sum(-1).sqrt().unsqueeze(-1)
                  if k > 0 else torch.zeros(X.shape[0], 1))
        rnd = torch.randn(X.shape[0], V.shape[1], generator=rng) @ V.T
        rnd = rnd / (rnd.norm(dim=-1, keepdim=True) + 1e-12) * energy
        d_rand = distortion(x_burnt + rnd)

        rows.append({"k": k, "ref_distortion": round(d_ref, 4),
                     "random_distortion": round(d_rand, 4)})
        if smallest_speck is None and d_ref < TARGET_FIDELITY:
            smallest_speck = k

    full_d = rows[-1]["ref_distortion"]
    report = {
        "title": "Σ₀ᴿ on a real log — put the smoke back, measured",
        "provenance": {
            "real_inputs": [
                f"{SOURCE} ({len(turns)} turns)",
                f"hashed token-bag embedding values (dim={DIM})",
                "least-squares fitted drift Jacobian A",
                "collapse certificate verdict and all distortion numbers",
            ],
            "designed_choices": [
                f"embedding dimension {DIM} and the hashing scheme",
                f"ridge constant {RIDGE}",
                f"target fidelity {TARGET_FIDELITY}",
            ],
            "not_claimed": [
                "reconstructs the EMBEDDED trajectory, not the original tokens",
                "lossy compression of dynamical structure, not text recovery",
                "the floor is the rate-distortion limit, not beaten",
            ],
        },
        "config": {"dim": DIM, "ridge": RIDGE, "eig_eps": EPS,
                   "target_fidelity": TARGET_FIDELITY, "seed": SEED, "source": SOURCE},
        "n_turns": len(turns),
        "collapse_certificate": cert.summary(),
        "collapse_guaranteed": bool(cert.guaranteed),
        "active_dim": active_dim,
        "null_dim": null_dim,
        "structure_energy_pre_burn": round(pre, 4),
        "structure_energy_post_burn": round(post, 8),
        "smallest_speck_modes": smallest_speck,
        "effective_dimension": smallest_speck,
        "speck_fraction_of_state": (None if smallest_speck is None
                                    else round(smallest_speck / DIM, 3)),
        "floor_distortion_full_seed": full_d,
        "p5_lossless_at_full_record": full_d < 1e-3,
        "curve": rows,
        "convergence_record": {
            "hypothesis": "A real log's active structure ('smoke') can be burned "
                          "and regrown from a compact seed, down to a hard floor.",
            "evidence": f"{len(turns)} turns, dim {DIM}; collapse "
                        f"{'guaranteed' if cert.guaranteed else 'not guaranteed'}; "
                        f"pre-burn structure {round(pre, 4)} → post-burn {round(post, 8)}; "
                        f"smallest speck {smallest_speck}/{active_dim} active modes; "
                        f"full-record distortion {full_d}.",
            "result": f"effective dimension = {smallest_speck} modes "
                      f"({'P5 lossless-at-full-record holds' if full_d < 1e-3 else 'full-record floor > 0'}).",
            "confidence": "observable 1.0 (every number measured); embedding designed.",
            "sources": [SOURCE, "src/cio_sde/collapse.py", ARTIFACT],
        },
    }

    os.makedirs(os.path.dirname(ARTIFACT), exist_ok=True)
    with open(ARTIFACT, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    # ── human-readable ──
    print("Σ₀ᴿ — putting the smoke back in a REAL log")
    print(f"  source: {SOURCE}  ({len(turns)} turns → {DIM}-dim trajectory)")
    print(f"  collapse: {cert.summary()}")
    print(f"  structure energy  pre-burn={pre:.4f}  post-burn={post:.2e}  "
          f"(active modes = the smoke)")
    print(f"  active/null dims: {active_dim}/{null_dim}")
    print()
    print(f"  {'seed k':>6} | {'reference (record)':>18} | {'random (no record)':>18}")
    print("  " + "-" * 50)
    for r in rows:
        mark = "  ← smallest speck" if r["k"] == smallest_speck else ""
        print(f"  {r['k']:>6} | {r['ref_distortion']:>18.4f} | "
              f"{r['random_distortion']:>18.4f}{mark}")
    print()
    if smallest_speck is not None:
        print(f"  smallest speck: {smallest_speck}/{active_dim} active modes "
              f"({report['speck_fraction_of_state']*100:.1f}% of the {DIM}-dim state) "
              f"rebuilds the real trajectory to within {int(TARGET_FIDELITY*100)}%.")
    print(f"  full-record floor distortion = {full_d}  "
          f"(P5 lossless-at-full-record: {report['p5_lossless_at_full_record']})")
    print(f"  effective dimension of the real log = {smallest_speck}")
    print(f"\n  artifact: {ARTIFACT}")


if __name__ == "__main__":
    main()
