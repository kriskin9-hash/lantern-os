"""
Kalshi council trainer — grade the historical capture into the Σ₀ council's
Converge stage, and honestly report whether any config is net-profitable AFTER fees.

This is the Kalshi arm of the trader council (docs/SIGMA0-EV-GATE.md). It does NOT
invent an edge: it replays the SAME momentum signal the live trader uses
(kalshi_cio_backtest.CIOConvergenceModel) over the recorded tight-band trajectories,
makes a fee-aware ENTER/SKIP call (mirroring apps/lantern-garage/lib/kalshi-fees.js),
settles each trade against the real resolution, and writes:

  1. data/kalshi/council-outcomes.jsonl   — one Brier-graded ConvergenceRecord per
     ENTERED trade, in the schema sigma0-trader-council.js already reads (so the
     council surface reflects real historical outcomes, not a cold prior). The model
     the council "uses" is the per-signal realized-edge table computed over these rows.
  2. data/kalshi/strategy-search-report.json — net-after-fee PnL for a SWEEP of
     configs (edge threshold × price band) + an honest verdict. The point of the sweep
     is to search for a +EV-after-fees config; the report tells the truth either way.
  3. data/kalshi/replay-outcomes.json  — ticker -> {finalYesMid, outcome} so the
     replay-deck endpoint can grade a swipe instantly without re-scanning GBs.
  4. data/kalshi/replay-deck.json — a sampled set of resolved markets (entry snapshot +
     metadata + final outcome) the replay-deck endpoint serves as swipeable cards.

External-Reality rule: every emitted row is a real realized outcome; confidence is the
model's own p_win so the council's calibration honestly exposes any over-confidence.

Run:  PYTHONIOENCODING=utf-8 python experiments/kalshi_council_train.py
      PYTHONIOENCODING=utf-8 python experiments/kalshi_council_train.py --limit-files 2  # fast
"""

from __future__ import annotations

import argparse
import glob
import json
import math
import random
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kalshi_cio_backtest import Snapshot, MarketTrajectory, CIOConvergenceModel  # noqa
from kalshi_pnl_backtest import kalshi_fee_cents, outcome_of, settle, RESOLVED_TH, MIN_POINTS  # noqa

REPO = Path(__file__).resolve().parents[1]
KALSHI_DIR = REPO / "data" / "kalshi"

COUNCIL_OUTCOMES = KALSHI_DIR / "council-outcomes.jsonl"
SEARCH_REPORT = KALSHI_DIR / "strategy-search-report.json"
REPLAY_OUTCOMES = KALSHI_DIR / "replay-outcomes.json"
REPLAY_DECK = KALSHI_DIR / "replay-deck.json"

SOURCE = "kalshi-backtest"
SEED = 12345
# How hard the momentum signal pulls the model's p_win away from the market price
# toward the certified endpoint. This is the model's (optimistic) conviction; the
# council's Brier calibration is what keeps it honest.
LAMBDA = 0.30
REPLAY_SAMPLE = 240   # markets to expose as replay cards


# ── fee model — mirrors apps/lantern-garage/lib/kalshi-fees.js exactly ──────────
STANDARD_MULTIPLIER = 0.07


def fee_fraction(price_cents: float, mult: float = STANDARD_MULTIPLIER) -> float:
    c = min(99, max(1, price_cents))
    p = c / 100.0
    return mult * p * (1 - p)


def breakeven_win_prob(price_cents: float, round_trip: bool = False) -> float:
    c = min(99, max(1, price_cents))
    p = c / 100.0
    return min(1.0, p + fee_fraction(price_cents) * (2 if round_trip else 1))


def net_ev_cents(price_cents: float, win_prob: float, round_trip: bool = False) -> float:
    p = min(99, max(1, price_cents)) / 100.0
    w = min(1.0, max(0.0, win_prob))
    fee = fee_fraction(price_cents) * (2 if round_trip else 1)
    return round(((w - p) - fee) * 100, 1)


def is_positive_ev(price_cents: float, win_prob: float, margin_frac: float = 0.0) -> bool:
    w = min(1.0, max(0.0, win_prob))
    return w > breakeven_win_prob(price_cents) + margin_frac


# ── enriched loader (keeps title/close_time for replay cards) ───────────────────
def load_enriched(files):
    """ticker -> {'pts': [(ts, ya, na)], 'title', 'close_ts', 'strike'}."""
    rows = defaultdict(lambda: {"pts": [], "title": None, "close_ts": None, "strike": None})
    for fp in files:
        with open(fp, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                ts = r.get("ts", "")
                for m in (r.get("snapshot", {}).get("markets") or []):
                    ya, na = m.get("yes_ask"), m.get("no_ask")
                    if ya is None or na is None:
                        continue
                    t = m.get("ticker")
                    rec = rows[t]
                    rec["pts"].append((ts, int(ya), int(na)))
                    if m.get("title"):
                        rec["title"] = m.get("title")
                    if m.get("close_time"):
                        rec["close_ts"] = m.get("close_time")
                    if m.get("floor_strike") is not None:
                        rec["strike"] = m.get("floor_strike")
    series = {}
    for t, rec in rows.items():
        rec["pts"].sort(key=lambda x: x[0])
        if len(rec["pts"]) >= MIN_POINTS:
            series[t] = rec
    return series


def mins_to_close(ts_iso, close_iso):
    try:
        a = datetime.fromisoformat(ts_iso.replace("Z", "+00:00"))
        b = datetime.fromisoformat(close_iso.replace("Z", "+00:00"))
        return round((b - a).total_seconds() / 60.0, 1)
    except Exception:
        return None


# ── first-signal entry per trajectory (one forward walk, no look-ahead) ─────────
def first_entry(pts, close_ts, model):
    """Return the first step the momentum signal fires, with the signal vector."""
    for i in range(MIN_POINTS, len(pts)):
        seen = pts[:i]
        snaps = [Snapshot(ya / 100.0, na / 100.0) for _, ya, na in seen]
        p_star, has = model.predict(MarketTrajectory(snaps, outcome=-1, close_ts=close_ts))
        if not has:
            continue
        price_now = snaps[-1].yes_mid
        edge = p_star - price_now          # signed; sign picks the side
        side_yes = edge > 0
        _, ya, na = seen[-1]
        entry = ya if side_yes else na
        if not (0 < entry < 100):
            return None
        spread = max(0, ya + na - 100)
        proj = abs(edge)
        p_market = entry / 100.0
        m2c = mins_to_close(seen[-1][0], close_ts)
        signals = {
            "momentum":    round(min(0.99, 0.5 + proj), 4),
            "convergence": round(p_market, 4),
            "time_band":   round(1 - min(1.0, (m2c or 240) / 240.0), 4) if m2c is not None else 0.5,
            "spread":      round(1 - min(1.0, spread / 20.0), 4),
        }
        return {
            "idx": i, "side_yes": side_yes, "entry": entry, "edge": round(abs(edge), 4),
            "spread": spread, "p_market": round(p_market, 4), "mins_to_close": m2c,
            "signals": signals,
        }
    return None


def p_win_model(p_market: float) -> float:
    """Model conviction: pull market price toward the certified (taken) endpoint."""
    return max(0.05, min(0.95, p_market + LAMBDA * (1 - p_market)))


# Config sweep: search for any +EV-after-fees corner of the space.
SWEEP = [
    {"name": "edge08_full",     "edge": 0.08, "band": (4, 96),  "margin": 0.0},
    {"name": "edge12_full",     "edge": 0.12, "band": (4, 96),  "margin": 0.0},
    {"name": "edge08_mid",      "edge": 0.08, "band": (20, 80), "margin": 0.0},
    {"name": "edge08_favband",  "edge": 0.08, "band": (60, 96), "margin": 0.0},
    {"name": "edge08_evmargin", "edge": 0.08, "band": (4, 96),  "margin": 0.02},
]
BASELINE = "edge08_full"


def config_includes(cfg, e):
    if e["edge"] <= cfg["edge"]:
        return False
    lo, hi = cfg["band"]
    if not (lo <= e["entry"] <= hi):
        return False
    return is_positive_ev(e["entry"], p_win_model(e["p_market"]), cfg["margin"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit-files", type=int, default=0, help="use only the N most recent crypto files (fast)")
    args = ap.parse_args()

    files = sorted(glob.glob(str(KALSHI_DIR / "crypto-tight-band-*.jsonl")))
    if args.limit_files > 0:
        files = files[-args.limit_files:]
    if not files:
        print("No crypto-tight-band files found.")
        return

    print(f"loading {len(files)} file(s)...")
    series = load_enriched(files)
    model = CIOConvergenceModel()

    entries = []          # one record per resolved market that produced a signal
    replay_outcomes = {}  # ticker -> {finalYesMid, outcome}
    replay_pool = []      # sampled cards
    resolved_n = 0

    rng = random.Random(SEED)

    for t, rec in series.items():
        pts = rec["pts"]
        traj = [(ya, na) for _, ya, na in pts]
        oc = outcome_of(traj)
        if oc == -1:
            continue
        resolved_n += 1
        final_ya, final_na = traj[-1]
        final_mid = round(final_ya / (final_ya + final_na), 4) if (final_ya + final_na) else 0.5
        replay_outcomes[t] = {"finalYesMid": final_mid, "outcome": oc}

        # replay card: an as-of snapshot ~40% through, where the decision is live
        as_of = max(MIN_POINTS - 1, int(len(pts) * 0.4))
        as_of = min(as_of, len(pts) - 1)
        ts_a, ya_a, na_a = pts[as_of]
        replay_pool.append({
            "ticker": t,
            "title": rec["title"] or t,
            "yesAsk": ya_a, "noAsk": na_a,
            "yesPct": round(ya_a / (ya_a + na_a) * 100) if (ya_a + na_a) else 50,
            "minsToClose": mins_to_close(ts_a, rec["close_ts"]),
            "closeTs": rec["close_ts"],
            "strike": rec["strike"],
            "outcome": oc,
        })

        e = first_entry(pts, rec["close_ts"], model)
        if e:
            e["ticker"] = t
            e["outcome"] = oc
            entries.append(e)

    # ── per-config net-after-fee sweep ──────────────────────────────────────────
    sweep_results = []
    for cfg in SWEEP:
        trades = []
        for e in entries:
            if not config_includes(cfg, e):
                continue
            net, won = settle(e["side_yes"], e["entry"], e["outcome"])
            trades.append((net, won))
        n = len(trades)
        net = sum(c for c, _ in trades)
        wins = sum(1 for _, w in trades if w)
        sweep_results.append({
            "name": cfg["name"], "edge": cfg["edge"], "band": list(cfg["band"]),
            "margin": cfg["margin"], "n": n,
            "win_pct": round(wins / n * 100, 1) if n else None,
            "net_cents": net, "net_usd": round(net / 100, 2),
            "avg_cents_per_trade": round(net / n, 2) if n else None,
        })

    best = max(sweep_results, key=lambda r: r["net_cents"]) if sweep_results else None
    # A real edge has to clear a MAGNITUDE bar, not just net>0: +0.1c/trade over a
    # fee-heavy market is break-even noise, not an edge. Require a half-cent per trade
    # after fees on a non-trivial sample before calling anything a candidate.
    MIN_EDGE_CPT = 0.5   # cents/trade after fees
    candidates = [r for r in sweep_results
                  if r["n"] >= 100 and (r["avg_cents_per_trade"] or 0) >= MIN_EDGE_CPT]
    if candidates:
        top = max(candidates, key=lambda r: r["avg_cents_per_trade"])
        verdict = (f"CANDIDATE EDGE: config '{top['name']}' clears the bar at "
                   f"{top['avg_cents_per_trade']:+}c/trade after fees ({top['net_usd']:+} USD, "
                   f"n={top['n']}). Validate strictly out-of-sample before any live use.")
    else:
        thin = best and best["net_cents"] > 0
        verdict = ("NO PROVEN EDGE: no swept config clears +0.5c/trade after fees on this "
                   "capture" + (f" (best is '{best['name']}' at {best['avg_cents_per_trade']:+}c/trade — "
                   "break-even noise, not an edge)" if thin else " — every config loses money") +
                   ". The 15-min crypto fee eats the win-rate. Live trading stays paused; this "
                   "surface is paper / data-collection only.")

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "files": len(files), "tickers": len(series), "resolved": resolved_n,
        "signals_fired": len(entries),
        "lambda": LAMBDA, "fee_model": "kalshi 0.07*p*(1-p), ceil per contract",
        "baseline_config": BASELINE,
        "sweep": sweep_results,
        "best": best,
        "verdict": verdict,
    }
    SEARCH_REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")

    # ── emit council outcomes for the BASELINE config (idempotent) ──────────────
    cfg = next(c for c in SWEEP if c["name"] == BASELINE)
    existing_ids = set()
    if COUNCIL_OUTCOMES.exists():
        for line in COUNCIL_OUTCOMES.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                existing_ids.add(json.loads(line).get("record_id"))
            except json.JSONDecodeError:
                continue

    emitted = 0
    with COUNCIL_OUTCOMES.open("a", encoding="utf-8") as out:
        for e in entries:
            if not config_includes(cfg, e):
                continue
            rid = f"kalshi-bt-{e['ticker']}-{e['idx']}"
            if rid in existing_ids:
                continue
            net, won = settle(e["side_yes"], e["entry"], e["outcome"])
            conf = round(p_win_model(e["p_market"]), 4)
            outcome = 1 if won else 0
            row = {
                "record_id": rid,
                "ticker": e["ticker"],
                "side": "yes" if e["side_yes"] else "no",
                "confidence": conf,
                "passed": bool(won),
                "outcome": outcome,
                "brier_score": round((conf - outcome) ** 2, 4),
                "pnl_pct": round(net / e["entry"] * 100, 2),
                "pnl_cents_after_fee": net,
                "signals": e["signals"],
                "source": SOURCE,
                "conviction_recorded": True,
                "graded_at": datetime.now(timezone.utc).isoformat(),
            }
            out.write(json.dumps(row) + "\n")
            emitted += 1

    # ── replay artefacts ────────────────────────────────────────────────────────
    REPLAY_OUTCOMES.write_text(json.dumps(replay_outcomes), encoding="utf-8")
    rng.shuffle(replay_pool)
    REPLAY_DECK.write_text(json.dumps(replay_pool[:REPLAY_SAMPLE], indent=2), encoding="utf-8")

    # ── console summary ─────────────────────────────────────────────────────────
    print(f"\nresolved={resolved_n}  signals_fired={len(entries)}  council_rows_emitted={emitted}")
    print("\n=== config sweep (net after fees) ===")
    for r in sweep_results:
        print(f"  {r['name']:16s} n={r['n']:4d}  win={r['win_pct']}%  "
              f"net=${r['net_usd']:+.2f}  avg={r['avg_cents_per_trade']}c")
    print(f"\nVERDICT: {verdict}")
    print(f"\nwrote: {COUNCIL_OUTCOMES.name}, {SEARCH_REPORT.name}, "
          f"{REPLAY_OUTCOMES.name}, {REPLAY_DECK.name} ({len(replay_pool[:REPLAY_SAMPLE])} replay cards)")


if __name__ == "__main__":
    main()
