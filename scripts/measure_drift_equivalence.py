"""
Measure cross-provider drift-equivalence for issue #845.

Σ₀-K1 build-out — 3/11. Spec: docs/SIGMA0-K1-KERNEL-SPEC.md §2

For each provider pair, runs N prompts, embeds the text responses as
sparse BOW vectors (proxy for φ-encoded x), and computes the relative
drift:

    drift = ‖f_old − f_new‖ / ‖f_old‖

where f_old = response vector from provider A, f_new = response vector
from provider B, on the same prompt x.

The full φ: hidden-state → x∈Rᵈ shim (component 6) is not yet built.
This script uses BOW response embeddings as a text-level proxy — honest
limitation documented in output.

NOTE: Requires cloud API keys in .env (ANTHROPIC_API_KEY, OPENAI_API_KEY,
GOOGLE_AI_API_KEY). Missing keys → provider is skipped, not crashed.

Run:
    python scripts/measure_drift_equivalence.py
    python scripts/measure_drift_equivalence.py --n 20 --tol 0.25

Outputs:
    data/eval/drift-equivalence-YYYY-MM-DD.json — full results
    Prints verdict table to stdout.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
import urllib.request
import urllib.error
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PROMPTS_PATH = REPO / "data" / "eval" / "sigma0-prompts.jsonl"
OUT_DIR = REPO / "data" / "eval"

DEFAULT_N = 10
DEFAULT_TOL = 0.25
TIMEOUT = 30  # seconds per API call


# ── BOW embedding proxy ───────────────────────────────────────────────────────

def _tokenize(text: str) -> list[str]:
    """Very light word-level tokenization for BOW proxy."""
    import re
    return re.findall(r"\b[a-z0-9]{2,}\b", text.lower())


def bow_vector(text: str) -> Counter:
    return Counter(_tokenize(text))


def cosine_similarity(a: Counter, b: Counter) -> float:
    if not a or not b:
        return 0.0
    dot = sum(a[k] * b[k] for k in a if k in b)
    mag_a = math.sqrt(sum(v * v for v in a.values()))
    mag_b = math.sqrt(sum(v * v for v in b.values()))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def relative_drift(v_old: Counter, v_new: Counter) -> float:
    """‖v_old − v_new‖ / ‖v_old‖ using L2 norm on BOW counters."""
    all_keys = set(v_old) | set(v_new)
    diff_sq = sum((v_old.get(k, 0) - v_new.get(k, 0)) ** 2 for k in all_keys)
    norm_old = math.sqrt(sum(v ** 2 for v in v_old.values()))
    if norm_old == 0:
        return float("inf")
    return math.sqrt(diff_sq) / norm_old


# ── Provider call stubs ───────────────────────────────────────────────────────

def _load_env() -> dict:
    env_path = REPO / ".env"
    env: dict = {}
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip().strip('"').strip("'")
    return {**env, **os.environ}


def _call_anthropic(prompt: str, env: dict) -> str | None:
    key = env.get("ANTHROPIC_API_KEY", "")
    if not key:
        return None
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=key)
        msg = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text if msg.content else ""
    except Exception as e:
        return f"[anthropic_error: {e}]"


def _call_openai(prompt: str, env: dict) -> str | None:
    key = env.get("OPENAI_API_KEY", "")
    if not key:
        return None
    try:
        import openai
        client = openai.OpenAI(api_key=key)
        resp = client.chat.completions.create(
            model="gpt-4.1-mini",
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
            timeout=TIMEOUT,
        )
        return resp.choices[0].message.content or ""
    except Exception as e:
        return f"[openai_error: {e}]"


def _call_gemini(prompt: str, env: dict) -> str | None:
    key = env.get("GOOGLE_AI_API_KEY", env.get("GEMINI_API_KEY", ""))
    if not key:
        return None
    try:
        import google.generativeai as genai
        genai.configure(api_key=key)
        model = genai.GenerativeModel("gemini-2.5-flash")
        resp = model.generate_content(prompt)
        return resp.text or ""
    except Exception as e:
        return f"[gemini_error: {e}]"


PROVIDERS = {
    "anthropic": _call_anthropic,
    "openai": _call_openai,
    "gemini": _call_gemini,
}


# ── Main measurement ──────────────────────────────────────────────────────────

def load_prompts(n: int) -> list[dict]:
    rows = []
    if not PROMPTS_PATH.exists():
        print(f"[warn] Prompts file not found: {PROMPTS_PATH}", file=sys.stderr)
        return []
    with PROMPTS_PATH.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    # prefer smoke + easy tier for speed
    rows.sort(key=lambda r: {"smoke": 0, "easy": 1, "med": 2, "hard": 3}.get(r.get("difficulty", "hard"), 4))
    return rows[:n]


def measure(n: int = DEFAULT_N, tol: float = DEFAULT_TOL, verbose: bool = False) -> dict:
    env = _load_env()
    prompts = load_prompts(n)
    if not prompts:
        return {"error": "no_prompts", "prompts_path": str(PROMPTS_PATH)}

    # Detect available providers
    available: dict[str, callable] = {}
    for name, fn in PROVIDERS.items():
        test_result = fn(prompts[0]["prompt"], env)
        if test_result is not None and not test_result.startswith("[") :
            available[name] = fn
            print(f"  provider {name}: ✓ available")
        elif test_result is None:
            print(f"  provider {name}: ✗ no key")
        else:
            print(f"  provider {name}: ✗ error — {test_result[:80]}")

    if len(available) < 2:
        return {
            "error": "insufficient_providers",
            "available": list(available.keys()),
            "message": "Need ≥2 providers with valid keys and working calls to measure drift.",
            "ts": datetime.now(timezone.utc).isoformat(),
        }

    provider_names = list(available.keys())
    pairs = [(provider_names[i], provider_names[j])
             for i in range(len(provider_names))
             for j in range(i + 1, len(provider_names))]

    print(f"\nRunning {len(prompts)} prompts across {len(pairs)} provider pair(s)…")

    # Collect responses
    responses: dict[str, list[str]] = {name: [] for name in available}
    for idx, row in enumerate(prompts):
        prompt = row["prompt"]
        if verbose:
            print(f"  [{idx+1}/{len(prompts)}] {prompt[:60]}…")
        for name, fn in available.items():
            t0 = time.time()
            reply = fn(prompt, env) or ""
            if reply.startswith("[") and "_error:" in reply:
                reply = ""
            responses[name].append(reply)
            if verbose:
                print(f"    {name}: {reply[:50]}… ({time.time()-t0:.1f}s)")

    # Compute drift per pair
    pair_results = []
    for pa, pb in pairs:
        drifts = []
        for r_a, r_b in zip(responses[pa], responses[pb]):
            v_a = bow_vector(r_a)
            v_b = bow_vector(r_b)
            if v_a or v_b:
                drifts.append(relative_drift(v_a, v_b))
        mean_drift = sum(drifts) / len(drifts) if drifts else float("inf")
        max_drift = max(drifts) if drifts else float("inf")
        equiv = mean_drift <= tol
        pair_results.append({
            "pair": f"{pa} × {pb}",
            "provider_a": pa,
            "provider_b": pb,
            "n_prompts": len(drifts),
            "mean_drift": round(mean_drift, 4),
            "max_drift": round(max_drift, 4),
            "tol": tol,
            "equivalent": equiv,
        })

    # Verdict
    all_equiv = all(r["equivalent"] for r in pair_results)
    any_equiv = any(r["equivalent"] for r in pair_results)

    verdict = "yes" if all_equiv else ("partial" if any_equiv else "no")
    # Per spec: "if no → diversity lives in the text re-prompt lane, not the VM"
    implication = (
        "hot-swap can be cross-provider (within tol)" if verdict == "yes"
        else "diversity should live in the text re-prompt lane (loop-reasoner.js), not the VM"
    )

    result = {
        "issue": "#845",
        "ts": datetime.now(timezone.utc).isoformat(),
        "n_prompts": len(prompts),
        "tol": tol,
        "proxy": "BOW text embedding (not φ: hidden-state → x; component 6 not yet built)",
        "providers_tested": list(available.keys()),
        "pairs": pair_results,
        "verdict": verdict,
        "implication": implication,
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Measure cross-provider drift-equivalence (#845)")
    parser.add_argument("--n", type=int, default=DEFAULT_N, help="Number of prompts to test")
    parser.add_argument("--tol", type=float, default=DEFAULT_TOL, help="Drift tolerance (default 0.25)")
    parser.add_argument("--out", help="Output JSON path (default: data/eval/drift-equivalence-DATE.json)")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    print(f"Measuring cross-provider drift-equivalence (n={args.n}, tol={args.tol})")
    print("Probing available providers…")
    result = measure(n=args.n, tol=args.tol, verbose=args.verbose)

    # Print summary
    print("\n" + "="*60)
    if "error" in result:
        print(f"ERROR: {result['error']} — {result.get('message', '')}")
        sys.exit(1)

    print(f"Providers tested: {', '.join(result['providers_tested'])}")
    print(f"Proxy: {result['proxy']}")
    print()
    print(f"{'Pair':<30} {'Mean drift':>12} {'Max drift':>12} {'≤tol?':>8}")
    print("-" * 70)
    for pr in result["pairs"]:
        mark = "✓" if pr["equivalent"] else "✗"
        print(f"{pr['pair']:<30} {pr['mean_drift']:>12.4f} {pr['max_drift']:>12.4f} {mark:>8}")
    print()
    print(f"Verdict: {result['verdict'].upper()}")
    print(f"Implication: {result['implication']}")

    # Write output
    out_path = args.out or str(OUT_DIR / f"drift-equivalence-{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.json")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\nResults written to: {out_path}")


if __name__ == "__main__":
    main()
