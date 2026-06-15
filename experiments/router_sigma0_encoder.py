"""
router_sigma0_encoder.py
========================
Encodes Lantern OS conversation logs into Σ₀ state vectors and fits local
Jacobians via finite difference.

State vector per turn:
  x = [novelty, self_repeat, echo, length] ∈ [0,1]⁴

  novelty     — fraction of tokens in this turn not seen in the previous turn
  self_repeat — mean bigram-overlap of this turn against all earlier turns
  echo        — cosine similarity between this turn and the prior AI turn
  length      — normalised message length (tanh(len/200))

Outputs:
  data/sigma0/router-encoder-output.jsonl  — one JSON object per turn

Prints a summary: n_turns, mean/max spectral radius, fraction above 1.0.

Run from repo root:
  python experiments/router_sigma0_encoder.py
"""

from __future__ import annotations

import json
import math
import os
import re
import sys
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np

# ── paths ─────────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parent.parent
CONV_DIR = REPO_ROOT / "apps" / "data" / "conversations"
OUT_DIR = REPO_ROOT / "data" / "sigma0"
OUT_FILE = OUT_DIR / "router-encoder-output.jsonl"

# ── tokenisation (simple whitespace + punctuation split) ──────────────────────

_SPLIT = re.compile(r"[^\w]+")


def tokenise(text: str) -> List[str]:
    return [t for t in _SPLIT.split(text.lower()) if t]


def bigrams(tokens: List[str]) -> set:
    return {(tokens[i], tokens[i + 1]) for i in range(len(tokens) - 1)}


# ── state-vector computation ───────────────────────────────────────────────────

def _cos_sim(a: List[str], b: List[str]) -> float:
    """TF cosine similarity between two token lists."""
    if not a or not b:
        return 0.0
    vocab = set(a) | set(b)
    v_a = np.array([a.count(w) for w in vocab], dtype=float)
    v_b = np.array([b.count(w) for w in vocab], dtype=float)
    na, nb = np.linalg.norm(v_a), np.linalg.norm(v_b)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(v_a, v_b) / (na * nb))


def state_vector(
    tokens: List[str],
    prev_tokens: Optional[List[str]],
    earlier_turns: List[List[str]],
    prior_ai_tokens: Optional[List[str]],
) -> np.ndarray:
    # novelty
    if prev_tokens:
        prev_set = set(prev_tokens)
        cur_set = set(tokens)
        novelty = len(cur_set - prev_set) / max(len(cur_set), 1)
    else:
        novelty = 1.0

    # self_repeat — mean bigram overlap with all earlier turns
    if earlier_turns:
        cur_bg = bigrams(tokens)
        overlaps = []
        for et in earlier_turns:
            et_bg = bigrams(et)
            union = len(cur_bg | et_bg)
            if union == 0:
                overlaps.append(0.0)
            else:
                overlaps.append(len(cur_bg & et_bg) / union)
        self_repeat = float(np.mean(overlaps))
    else:
        self_repeat = 0.0

    # echo — cosine sim with prior AI turn
    echo = _cos_sim(tokens, prior_ai_tokens) if prior_ai_tokens else 0.0

    # length — tanh-normalised
    length = float(math.tanh(len(tokens) / 200.0))

    return np.array([novelty, self_repeat, echo, length], dtype=float)


# ── Jacobian fitting via finite difference ────────────────────────────────────

def fit_jacobian(states: np.ndarray) -> Optional[np.ndarray]:
    """
    Fit a local linear map  Δx_{t+1} ≈ J · Δx_t  over a window of states.
    states: (N, 4)
    Returns J (4x4) or None if too few points.
    """
    if len(states) < 5:
        return None

    # Build Δx pairs
    dx = np.diff(states, axis=0)          # (N-1, 4)
    X = dx[:-1]                            # inputs   (N-2, 4)
    Y = dx[1:]                             # outputs  (N-2, 4)

    if X.shape[0] < 4:
        return None

    # Least-squares:  Y = X @ J^T  → J^T = pinv(X) @ Y
    J_T, _, _, _ = np.linalg.lstsq(X, Y, rcond=None)
    return J_T.T


# ── load conversation logs ─────────────────────────────────────────────────────

def load_turns() -> List[dict]:
    turns = []
    jsonl_files = sorted(CONV_DIR.glob("*.jsonl")) if CONV_DIR.exists() else []
    for f in jsonl_files:
        with open(f, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                text = obj.get("text") or obj.get("content") or obj.get("message") or ""
                if not text:
                    continue
                role = obj.get("role", "unknown")
                turns.append({"role": role, "text": text, "ts": obj.get("recordedAt", "")})
    return turns


def synthetic_turns() -> List[dict]:
    """Fallback: 20 synthetic turns if no real logs found."""
    import random
    rng = random.Random(42)
    pool = [
        "The lantern flickers in the dream corridor.",
        "I keep seeing the same door repeated.",
        "There is a spiral staircase that never ends.",
        "The water reflects a face I don't recognise.",
        "Something is chasing me through a forest of mirrors.",
        "I woke up inside the dream again.",
        "The light at the end keeps moving further away.",
        "Voices repeat my own words back to me.",
        "The map shows only roads I have already walked.",
        "I ask the figure a question and it answers with my question.",
    ]
    turns = []
    for i in range(20):
        role = "operator" if i % 2 == 0 else "lantern"
        text = rng.choice(pool)
        if rng.random() > 0.5:
            text += " " + rng.choice(pool)
        turns.append({"role": role, "text": text, "ts": f"synthetic-{i:03d}"})
    return turns


# ── main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    turns = load_turns()
    if not turns:
        print("[router_sigma0_encoder] No conversation logs found — using 20 synthetic turns.")
        turns = synthetic_turns()
    else:
        print(f"[router_sigma0_encoder] Loaded {len(turns)} turns from {CONV_DIR}")

    # Per-turn state computation
    records = []
    all_tokens: List[List[str]] = []
    ai_roles = {"lantern", "blinkbug", "keystone", "waterfall", "xenon", "founder",
                "assistant", "ai"}
    prior_ai_tokens: Optional[List[str]] = None

    for i, turn in enumerate(turns):
        tokens = tokenise(turn["text"])
        prev_tokens = all_tokens[-1] if all_tokens else None
        earlier = all_tokens[:-1] if len(all_tokens) > 1 else []

        sv = state_vector(tokens, prev_tokens, earlier, prior_ai_tokens)
        records.append({
            "turn_idx": i,
            "role": turn["role"],
            "ts": turn["ts"],
            "state": sv.tolist(),
        })

        all_tokens.append(tokens)
        if turn["role"].lower() in ai_roles:
            prior_ai_tokens = tokens

    # Sliding-window Jacobian fitting (window = 10 turns)
    WINDOW = 10
    spectral_radii = []
    states_array = np.array([r["state"] for r in records])

    for i, rec in enumerate(records):
        start = max(0, i - WINDOW + 1)
        window_states = states_array[start : i + 1]
        J = fit_jacobian(window_states)
        if J is not None:
            eigvals = np.linalg.eigvals(J)
            rho = float(np.max(np.abs(eigvals)))
        else:
            rho = float("nan")
        rec["jacobian_spectral_radius"] = rho
        if not math.isnan(rho):
            spectral_radii.append(rho)

    # Write output
    with open(OUT_FILE, "w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec) + "\n")

    # Summary
    if spectral_radii:
        arr = np.array(spectral_radii)
        mean_rho = float(np.mean(arr))
        max_rho = float(np.max(arr))
        frac_above_1 = float(np.mean(arr > 1.0))
    else:
        mean_rho = max_rho = frac_above_1 = float("nan")

    print(f"\n=== router_sigma0_encoder summary ===")
    print(f"  n_turns               : {len(records)}")
    print(f"  turns with Jacobian   : {len(spectral_radii)}")
    print(f"  mean spectral radius  : {mean_rho:.4f}")
    print(f"  max  spectral radius  : {max_rho:.4f}")
    print(f"  fraction rho > 1.0    : {frac_above_1:.4f}")
    print(f"  output                : {OUT_FILE}")


if __name__ == "__main__":
    main()
