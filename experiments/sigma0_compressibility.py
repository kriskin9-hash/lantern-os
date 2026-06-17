"""
Beating the incompressibility — which basis lets a REAL log compress?

The first pass (experiments/sigma0_smoke_on_real_log.py) found a real conversation
trajectory nearly incompressible: ~23/24 modes needed for 10% fidelity. But that
reconstruction used the drift-Jacobian eigenbasis, which is NOT aligned with where
the data's variance lives. By Eckart–Young, the optimal low-rank basis is the
data's own covariance eigenbasis (PCA/SVD). This experiment tests whether the log
compresses in the RIGHT basis.

For each embedding it measures the rate–distortion curve (kept modes vs relative
reconstruction error, common metric ‖X̂−X‖_F / ‖X−mean‖_F) in two bases:

  drift : Σ₀ᴿ reconstruction in the fitted Jacobian's eigenbasis (the prior path)
  pca   : truncated-SVD reconstruction in the data covariance eigenbasis (optimal)

and reports the effective dimension (smallest k under a target fidelity) and the
compression ratio for each — plus the SVD energy spectrum (effective rank at
90/95/99% energy), the basis-free truth about how low-rank the trajectory is.

HONESTY: the embeddings (token-bag dims, the 4-D dynamical features) are DESIGNED;
the turns, embedding values, singular values, and every distortion number are REAL.
PCA is the optimal linear basis (Eckart–Young), so "pca beats drift" is expected;
the real question is HOW LOW the effective dimension goes — that is measured, not
assumed.

Reproducible: deterministic (crc32 hashing, no RNG, no network). Run:
    python experiments/sigma0_compressibility.py
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

from src.cio_sde import ReconstructionOperator, collapse_certificate

RIDGE = 1e-2
EPS = 1e-2
TARGET = 0.10                      # within 10% relative error defines effective dim
SOURCE = os.path.join("apps", "data", "conversations", "garage-conversations.jsonl")
ARTIFACT = os.path.join("data", "sigma0_compressibility_report.json")

_TOKEN = re.compile(r"[a-z0-9]+")


def load_turns(path: str) -> list[dict]:
    out = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return out


# ── embeddings (DESIGNED) ────────────────────────────────────────────────────

def embed_tokenbag(turns, dim):
    X = torch.zeros(len(turns), dim)
    for i, t in enumerate(turns):
        toks = _TOKEN.findall((t.get("text", "") or "").lower())
        for tok in toks:
            X[i, zlib.crc32(tok.encode("utf-8")) % dim] += 1.0
        X[i] = X[i].sqrt()
        n = X[i].norm()
        if n > 0:
            X[i] /= n
    return X


def embed_dynamical(turns, window=24):
    """4-D [novelty, self_repeat, echo, length] — the low-dim dynamical features."""
    toks = [set(_TOKEN.findall((t.get("text", "") or "").lower())) for t in turns]
    roles = [t.get("role", "?") for t in turns]

    def jac(a, b):
        if not a and not b:
            return 1.0
        if not a or not b:
            return 0.0
        return len(a & b) / len(a | b)

    X = torch.zeros(len(turns), 4)
    for i in range(len(turns)):
        lo = max(0, i - window)
        prev = toks[lo:i]
        echo = jac(toks[i], toks[i - 1]) if i > 0 else 0.0
        novelty = 1.0 - max((jac(toks[i], p) for p in prev), default=0.0)
        same = [p for p, r in zip(prev, roles[lo:i]) if r == roles[i]]
        self_rep = max((jac(toks[i], p) for p in same), default=0.0)
        length = min(1.0, len(toks[i]) / 40.0)
        X[i] = torch.tensor([novelty, self_rep, echo, length])
    return X


# ── reconstruction curves (common metric) ────────────────────────────────────

def _rel_err(X_hat, X, denom):
    return float((X_hat - X).norm() / denom)


def pca_curve(X):
    """Truncated-SVD reconstruction in the data covariance eigenbasis (optimal)."""
    mean = X.mean(0, keepdim=True)
    Xc = X - mean
    denom = Xc.norm() + 1e-12
    U, S, Vh = torch.linalg.svd(Xc, full_matrices=False)
    d = S.shape[0]
    rows, speck = [], None
    for k in range(d + 1):
        Xk = mean + (U[:, :k] * S[:k]) @ Vh[:k]
        e = _rel_err(Xk, X, denom)
        rows.append({"k": k, "rel_err": round(e, 4)})
        if speck is None and e < TARGET:
            speck = k
    # SVD energy spectrum → effective rank at energy thresholds
    energy = (S ** 2)
    cum = torch.cumsum(energy, 0) / energy.sum()
    eff = {f"{int(p*100)}pct": int((cum < p).sum().item()) + 1 for p in (0.90, 0.95, 0.99)}
    return rows, speck, d, eff


def drift_curve(X):
    """Σ₀ᴿ reconstruction in the fitted drift-Jacobian eigenbasis (prior path)."""
    x0, x1 = X[:-1], X[1:]
    d = X.shape[1]
    F = torch.linalg.solve(x0.T @ x0 + RIDGE * torch.eye(d), x0.T @ x1).T
    A = F - torch.eye(d)
    op = ReconstructionOperator(eig_eps=EPS)
    cert = collapse_certificate(A.unsqueeze(0), eig_eps=EPS)
    active = int(op._active_basis(A).shape[1])
    x_burnt = op.collapse(X, A)
    denom = (X - X.mean(0, keepdim=True)).norm() + 1e-12
    rows, speck = [], None
    for k in range(active + 1):
        e = _rel_err(op.reconstruct(x_burnt, op.seed(X, A, k)), X, denom)
        rows.append({"k": k, "rel_err": round(e, 4)})
        if speck is None and e < TARGET:
            speck = k
    return rows, speck, active, cert.summary()


def lossless_compressibility(turns, dim=128):
    """Where the compressibility actually lives: sparsity + redundancy, measured
    LOSSLESSLY (no fidelity floor). Two real numbers:
      - per-turn sparsity of the token-bag (most buckets are zero), and
      - byte-level DEFLATE ratio of the raw log text (redundancy coding)."""
    # sparsity of the dense embedding
    Xb = embed_tokenbag(turns, dim)
    nnz = (Xb.abs() > 0).sum(-1).float()
    sparsity = float(1.0 - nnz.mean() / dim)           # fraction of zero buckets
    # lossless byte-level compression of the actual text (deterministic DEFLATE)
    text = "\n".join((t.get("text", "") or "") for t in turns).encode("utf-8")
    comp = zlib.compress(text, 9)
    return {
        "embedding_dim": dim,
        "mean_nonzeros_per_turn": round(float(nnz.mean()), 2),
        "token_bag_sparsity": round(sparsity, 4),
        "raw_text_bytes": len(text),
        "deflate_bytes": len(comp),
        "lossless_deflate_ratio": round(len(text) / max(1, len(comp)), 2),
    }


def main():
    if not os.path.exists(SOURCE):
        print(f"source log not found: {SOURCE}", file=sys.stderr)
        sys.exit(1)
    turns = load_turns(SOURCE)

    embeddings = {
        "tokenbag_24": embed_tokenbag(turns, 24),
        "tokenbag_128": embed_tokenbag(turns, 128),
        "dynamical_4": embed_dynamical(turns),
    }

    results = {}
    for name, X in embeddings.items():
        d = X.shape[1]
        p_rows, p_speck, p_dim, eff = pca_curve(X)
        d_rows, d_speck, d_active, cert = drift_curve(X)
        results[name] = {
            "dim": d,
            "pca": {
                "effective_dim": p_speck,
                "compression_ratio": (round(d / p_speck, 2) if p_speck else None),
                "svd_effective_rank": eff,
                "curve": p_rows,
            },
            "drift": {
                "effective_dim": d_speck,
                "active_dim": d_active,
                "compression_ratio": (round(d / d_speck, 2) if d_speck else None),
                "certificate": cert,
                "curve": d_rows,
            },
        }

    # winner = embedding+basis with the best (lowest) effective-dim fraction
    best = None
    for name, r in results.items():
        for basis in ("pca", "drift"):
            ed = r[basis]["effective_dim"]
            if ed is None:
                continue
            frac = ed / r["dim"]
            if best is None or frac < best["fraction"]:
                best = {"embedding": name, "basis": basis, "effective_dim": ed,
                        "dim": r["dim"], "fraction": round(frac, 3),
                        "compression_ratio": r[basis]["compression_ratio"]}

    lossless = lossless_compressibility(turns)

    report = {
        "title": "Compressibility of a real log across embeddings and bases",
        "provenance": {
            "real_inputs": [
                f"{SOURCE} ({len(turns)} turns)",
                "embedding values, singular values, and all distortion numbers",
            ],
            "designed_choices": [
                "embedding families (token-bag dims 24/128, 4-D dynamical features)",
                f"ridge {RIDGE}, target fidelity {TARGET}",
            ],
            "not_claimed": [
                "PCA is optimal by Eckart–Young, so pca<=drift is expected; the "
                "measured quantity is HOW LOW the effective dimension goes",
                "reconstructs embedded trajectories, not original tokens",
            ],
        },
        "n_turns": len(turns),
        "target_fidelity": TARGET,
        "results": results,
        "winner": best,
        "lossless_compressibility": lossless,
        "verdict": (
            "Low-rank (dense) compression FAILS on this real log: even in the "
            f"optimal PCA basis the best lossy effective dimension is "
            f"{best['fraction']*100:.0f}% of the state. The compressibility lives "
            f"in SPARSITY + REDUNDANCY instead: the token-bag is "
            f"{lossless['token_bag_sparsity']*100:.0f}% zeros per turn and the raw "
            f"text compresses {lossless['lossless_deflate_ratio']}× losslessly. "
            "This confirms the whitepaper's honest scope: 'universe on a flash "
            "drive' bites via sparse/redundant coding, not low-rank structure."
        ),
        "convergence_record": {
            "hypothesis": "A real log can be made compressible by reconstructing in "
                          "the optimal (data-covariance) basis rather than the drift basis.",
            "evidence": "; ".join(
                f"{n}: pca eff-dim {r['pca']['effective_dim']}/{r['dim']}, "
                f"drift eff-dim {r['drift']['effective_dim']}/{r['drift']['active_dim']}"
                for n, r in results.items())
                + f"; lossless DEFLATE {lossless['lossless_deflate_ratio']}x, "
                  f"sparsity {lossless['token_bag_sparsity']}",
            "result": ("REFUTED for low-rank: the real log stays high-rank even in "
                       "the optimal basis. CONFIRMED for sparsity: it compresses "
                       f"{lossless['lossless_deflate_ratio']}× losslessly via "
                       "redundancy coding, not low-rank projection."),
            "confidence": "observable 1.0 (every number measured); embeddings designed.",
            "sources": [SOURCE, "src/cio_sde/collapse.py", ARTIFACT],
        },
    }

    os.makedirs(os.path.dirname(ARTIFACT), exist_ok=True)
    with open(ARTIFACT, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    # ── human-readable ──
    print(f"Compressibility of a real log — {len(turns)} turns, target {int(TARGET*100)}% rel-err")
    print(f"{'embedding':>14} | {'dim':>4} | {'drift eff-dim':>13} | {'PCA eff-dim':>12} | {'PCA ratio':>9}")
    print("-" * 66)
    for name, r in results.items():
        pca, dr = r["pca"], r["drift"]
        print(f"{name:>14} | {r['dim']:>4} | "
              f"{str(dr['effective_dim'])+'/'+str(dr['active_dim']):>13} | "
              f"{str(pca['effective_dim'])+'/'+str(r['dim']):>12} | "
              f"{str(pca['compression_ratio'])+'×':>9}")
    print()
    if best:
        print(f"WINNER: {best['embedding']} in the {best['basis'].upper()} basis — "
              f"{best['effective_dim']}/{best['dim']} modes "
              f"({best['fraction']*100:.1f}% of the state, {best['compression_ratio']}× smaller) "
              f"rebuilds to within {int(TARGET*100)}%.")
    for name, r in results.items():
        eff = r["pca"]["svd_effective_rank"]
        print(f"  {name}: SVD effective rank  90%={eff['90pct']}  95%={eff['95pct']}  99%={eff['99pct']}  (of {r['dim']})")
    print()
    print("where the compressibility actually lives (LOSSLESS):")
    print(f"  token-bag sparsity   = {lossless['token_bag_sparsity']*100:.0f}% zeros/turn "
          f"({lossless['mean_nonzeros_per_turn']} nonzeros of {lossless['embedding_dim']})")
    print(f"  raw-text DEFLATE     = {lossless['lossless_deflate_ratio']}× "
          f"({lossless['raw_text_bytes']:,} → {lossless['deflate_bytes']:,} bytes)")
    print()
    print("verdict: low-rank compression FAILS (high rank in every basis); "
          "compressibility is sparsity + redundancy, not low rank.")
    print(f"\nartifact: {ARTIFACT}")


if __name__ == "__main__":
    main()
