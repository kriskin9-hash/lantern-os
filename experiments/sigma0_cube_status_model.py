"""
Σ₀ Status-Cube Interpreter — a low-rank ("LoRA"), compressed model over the CSF
status cube. Provider-agnostic: it reads `lantern.cube_delta.v1` deltas from ANY
surface (journal, explore, dream-chat, kalshi, …). Kalshi is just one
`source_surface` feeding the cube via PCSF — never special-cased here.

WHAT IT IS (Σ₀-consistent, no foundation-model retraining):
  1. Encode each delta → a feature vector (surface, event_type, coordinate root,
     hashed symbol bag, recency).
  2. COMPRESS: truncated SVD gives the rank-k active-mode basis V_k — the Σ₀
     "seed". Each delta's status code = X·V_kᵀ. The rate–distortion curve (recon
     error vs k) is the measured compression floor.
  3. INTERPRET + LoRA-TUNE: a LOW-RANK head W = A·Bᵀ (rank r) maps the running
     cube status (EWMA of codes) → the next delta's event_type. Held out by time;
     graded honestly against the most-frequent baseline. A low-rank adapter is
     literally A·Bᵀ — the "LoRA" of the request, here over the cube not an LLM.
  4. SAVE compressed: V_k + head + vocab → a small .npz, plus a PCSF descriptor.
     Reports raw-cube-bytes ÷ model-bytes.

Honest by construction: tiny, imbalanced cube (journal-dominated) ⇒ the baseline
is strong; the report states plainly whether the model beats it. The reliable
deliverable is the compression floor, not a fabricated predictive edge.

Deterministic, numpy-only. Run:  python experiments/sigma0_cube_status_model.py
"""
from __future__ import annotations

import glob
import json
import os
import sys
import zlib

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CUBES_GLOB = os.path.join(REPO, "data", "cubes", "*", "deltas", "deltas.jsonl")
OUT_MODEL = os.path.join(REPO, "data", "cubes", "cube-status-model.npz")
OUT_PCSF = os.path.join(REPO, "data", "pcsf", "cube-status-model.pcsf.json")
OUT_REPORT = os.path.join(REPO, "data", "sigma0_cube_status_report.json")

SYMBOL_HASH_DIM = 48
DEFAULT_RANK = 8          # status-code rank k (the compressed dimension)
HEAD_RANK = 3             # LoRA adapter rank r on the interpreter head
EWMA = 0.6                # running-status smoothing
RIDGE = 1.0
SEED = 0

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass


# ── load ──────────────────────────────────────────────────────────────────────
def load_deltas(paths):
    """Chronological deltas across all cubes/surfaces (utf-8-sig: cube files
    carry a BOM)."""
    rows = []
    for p in paths:
        try:
            fh = open(p, encoding="utf-8-sig")
        except OSError:
            continue
        with fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if r.get("schema", "").startswith("lantern.cube_delta"):
                    rows.append(r)
    rows.sort(key=lambda r: r.get("created_at", ""))
    return rows


def _hash_symbols(symbols, dim):
    v = np.zeros(dim)
    for s in symbols or []:
        # zlib.crc32 is process-stable (unlike hash()) → reproducible model
        h = zlib.crc32(("sym:" + str(s)).encode("utf-8")) % dim
        v[h] += 1.0
    n = np.linalg.norm(v)
    return v / n if n > 0 else v


def build_vocab(rows):
    surf, ev, croot = {}, {}, {}
    for r in rows:
        surf.setdefault(r.get("source_surface", "?"), len(surf))
        ev.setdefault(r.get("event_type", "?"), len(ev))
        croot.setdefault((r.get("coordinate") or "?").split(":")[0], len(croot))
    return surf, ev, croot


def encode(rows, vocab):
    surf, ev, croot = vocab
    H = SYMBOL_HASH_DIM
    D = len(surf) + len(ev) + len(croot) + H + 1
    X = np.zeros((len(rows), D))
    for i, r in enumerate(rows):
        off = 0
        X[i, off + surf[r.get("source_surface", "?")]] = 1.0; off += len(surf)
        X[i, off + ev[r.get("event_type", "?")]] = 1.0; off += len(ev)
        X[i, off + croot[(r.get("coordinate") or "?").split(":")[0]]] = 1.0; off += len(croot)
        X[i, off:off + H] = _hash_symbols(r.get("symbols"), H); off += H
        X[i, off] = 1.0  # bias
    return X


# ── compress: rank-k active-mode basis (the Σ₀ seed) ─────────────────────────
def low_rank_basis(Xc, k):
    # Xc is centered. SVD → top-k right singular vectors (k × D).
    U, S, Vt = np.linalg.svd(Xc, full_matrices=False)
    k = min(k, Vt.shape[0])
    return Vt[:k], S


def rate_distortion(Xc, kmax):
    U, S, Vt = np.linalg.svd(Xc, full_matrices=False)
    total = float((Xc ** 2).sum())
    curve = []
    for k in range(1, min(kmax, len(S)) + 1):
        recon = (U[:, :k] * S[:k]) @ Vt[:k]
        err = float(((Xc - recon) ** 2).sum()) / total if total > 0 else 0.0
        curve.append({"k": k, "residual_frac": round(err, 5),
                      "energy_kept": round(1 - err, 5)})
    return curve


# ── LoRA-tuned interpreter head ──────────────────────────────────────────────
def running_status(codes, alpha):
    """EWMA of status codes → the cube's running status BEFORE each step."""
    out = np.zeros_like(codes)
    s = np.zeros(codes.shape[1])
    for i in range(len(codes)):
        out[i] = s            # status as of just-before delta i
        s = alpha * s + (1 - alpha) * codes[i]
    return out


def ridge_fit(Xs, Y, lam):
    d = Xs.shape[1]
    A = Xs.T @ Xs + lam * np.eye(d)
    return np.linalg.solve(A, Xs.T @ Y)         # (d × C)


def lora_truncate(W, r):
    """Compress the head to a rank-r adapter W ≈ A·Bᵀ (the 'LoRA')."""
    U, S, Vt = np.linalg.svd(W, full_matrices=False)
    r = min(r, len(S))
    A = U[:, :r] * S[:r]            # (d × r)
    B = Vt[:r].T                    # (C × r)
    return A, B, (A @ B.T)


def main():
    np.random.seed(SEED)
    paths = sorted(glob.glob(CUBES_GLOB))
    rows = load_deltas(paths)
    if len(rows) < 20:
        print(f"Not enough deltas ({len(rows)}). Need ≥20.")
        return

    vocab = build_vocab(rows)
    surf, ev, croot = vocab
    X = encode(rows, vocab)
    mean = X.mean(0)
    Xc = X - mean

    # provider mix (kalshi would appear here as one surface among many)
    mix = {s: int((np.array([r.get("source_surface") for r in rows]) == s).sum())
           for s in surf}

    # ── compression floor ──
    Vk, S = low_rank_basis(Xc, DEFAULT_RANK)
    codes = Xc @ Vk.T
    rd = rate_distortion(Xc, kmax=16)
    energy_at_k = next(c["energy_kept"] for c in rd if c["k"] == min(DEFAULT_RANK, len(S)))

    # ── interpreter: predict next event_type from running status ──
    status = running_status(codes, EWMA)
    ev_inv = {i: name for name, i in ev.items()}
    y_idx = np.array([ev[r.get("event_type", "?")] for r in rows])
    Y = np.eye(len(ev))[y_idx]
    # predict delta i's event_type from status-before-i; shift so target is "next"
    Xs, Yt, yt_idx = status[1:], Y[1:], y_idx[1:]
    n = len(Xs)
    n_val = max(4, n // 5)
    Xtr, Ytr = Xs[:-n_val], Yt[:-n_val]
    Xva, yva = Xs[-n_val:], yt_idx[-n_val:]

    W = ridge_fit(Xtr, Ytr, RIDGE)                     # full head (k × C)
    A, B, Wr = lora_truncate(W, HEAD_RANK)             # LoRA rank-r head
    pred_full = (Xva @ W).argmax(1)
    pred_lora = (Xva @ Wr).argmax(1)
    # most-frequent baseline (from training targets)
    base_cls = np.bincount(y_idx[1:][:-n_val], minlength=len(ev)).argmax()
    acc = lambda p: float((p == yva).mean())
    acc_full, acc_lora, acc_base = acc(pred_full), acc((Xva @ Wr).argmax(1)), float((base_cls == yva).mean())

    beats = acc_lora > acc_base + 1e-9
    verdict = "LoRA head BEATS most-frequent baseline" if beats else \
              "no better than most-frequent baseline (cube too imbalanced/small)"

    # ── compress + save the model ──
    np.savez_compressed(OUT_MODEL, mean=mean, Vk=Vk, A=A, B=B,
                        surf=json.dumps(surf), ev=json.dumps(ev),
                        croot=json.dumps(croot), ewma=EWMA)
    raw_bytes = sum(os.path.getsize(p) for p in paths if os.path.exists(p))
    model_bytes = os.path.getsize(OUT_MODEL)
    ratio = round(raw_bytes / model_bytes, 2) if model_bytes else 0.0

    report = {
        "title": "Σ₀ status-cube interpreter — low-rank, compressed",
        "provenance": {
            "real_inputs": [f"{len(rows)} deltas from {len(paths)} cube(s): "
                            + ", ".join(os.path.relpath(p, REPO) for p in paths)],
            "designed_choices": [f"rank k={DEFAULT_RANK}, LoRA head rank r={HEAD_RANK}, "
                                 f"symbol-hash dim={SYMBOL_HASH_DIM}, EWMA={EWMA}"],
            "not_claimed": ["no foundation-model weights touched; this is a low-rank "
                            "index/interpreter over the cube, not LLM retraining"],
        },
        "provider_mix": mix,
        "feature_dim": int(X.shape[1]),
        "compression": {
            "status_code_rank": int(Vk.shape[0]),
            "energy_kept_at_k": energy_at_k,
            "rate_distortion": rd,
            "raw_cube_bytes": raw_bytes,
            "model_bytes": model_bytes,
            "compression_ratio": ratio,
        },
        "interpreter": {
            "task": "predict next delta event_type from running cube status",
            "n_val": int(n_val),
            "acc_full_head": round(acc_full, 4),
            "acc_lora_head": round(acc_lora, 4),
            "acc_baseline_most_frequent": round(acc_base, 4),
            "lora_head_rank": HEAD_RANK,
            "head_params_full": int(W.size),
            "head_params_lora": int(A.size + B.size),
            "verdict": verdict,
        },
        "convergence_record": {
            "hypothesis": "The status cube has low effective dimension; a low-rank "
                          "(LoRA) interpreter can compress it and read its status.",
            "evidence": f"rank-{Vk.shape[0]} basis keeps {energy_at_k:.0%} of cube "
                        f"energy; model compresses {raw_bytes}B→{model_bytes}B "
                        f"({ratio}×); next-event acc lora={acc_lora:.2f} vs "
                        f"baseline={acc_base:.2f}.",
            "result": verdict + "; compression floor is the reliable signal.",
            "confidence": "observable 1.0 (measured, held-out by time)",
            "sources": ["experiments/sigma0_cube_status_model.py", OUT_REPORT, OUT_MODEL],
        },
    }
    os.makedirs(os.path.dirname(OUT_REPORT), exist_ok=True)
    with open(OUT_REPORT, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    # PCSF descriptor (component-style, like the other .pcsf.json files)
    pcsf = {
        "pcsf_type": "model", "pcsf_version": "2.0.0", "component": "cube-status-model",
        "description": "Low-rank (LoRA), compressed interpreter over the CSF status "
                       "cube. Provider-agnostic — Kalshi is one source_surface.",
        "generated_at": rows[-1].get("created_at", ""),
        "state": "available",
        "artifact": os.path.relpath(OUT_MODEL, REPO).replace(os.sep, "/"),
        "status_code_rank": int(Vk.shape[0]), "lora_head_rank": HEAD_RANK,
        "energy_kept": energy_at_k, "compression_ratio": ratio,
        "provider_mix": mix,
        "interpreter_acc": {"lora": round(acc_lora, 4), "baseline": round(acc_base, 4)},
    }
    os.makedirs(os.path.dirname(OUT_PCSF), exist_ok=True)
    with open(OUT_PCSF, "w", encoding="utf-8") as f:
        json.dump(pcsf, f, indent=2)

    # ── human-readable ──
    print(f"Σ₀ status-cube interpreter   ({len(rows)} deltas, {len(paths)} cube(s))")
    print(f"  provider mix       : {mix}")
    print(f"  feature dim        : {X.shape[1]}  → status-code rank k={Vk.shape[0]}")
    print(f"  energy kept @ k={Vk.shape[0]:>2}  : {energy_at_k:.1%}")
    print("  rate–distortion (k → energy kept):")
    for c in rd[:10]:
        print(f"      k={c['k']:>2}  energy_kept={c['energy_kept']:.3f}")
    print(f"  compression        : {raw_bytes:,}B → {model_bytes:,}B  ({ratio}×)")
    print(f"  LoRA head          : rank {HEAD_RANK}  "
          f"({W.size}→{A.size + B.size} params)")
    print(f"  next-event acc     : lora={acc_lora:.2f}  full={acc_full:.2f}  "
          f"baseline={acc_base:.2f}")
    print(f"  verdict            : {verdict}")
    print(f"\n  saved model  -> {os.path.relpath(OUT_MODEL, REPO)}")
    print(f"  saved pcsf   -> {os.path.relpath(OUT_PCSF, REPO)}")
    print(f"  saved report -> {os.path.relpath(OUT_REPORT, REPO)}")


if __name__ == "__main__":
    main()
