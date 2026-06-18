"""
Kalshi MAKER limit-order backtest (#694) — does posting inside the spread (vs
taking the ask) produce an edge after fees, accounting for FILL PROBABILITY?

The taker version (kalshi_pnl_backtest.py) loses on every strategy because you
pay the spread + 7% fee. A maker captures the spread instead of paying it — BUT
only gets filled when the market trades to your price, and tends to be filled
exactly when the move goes against you (adverse selection). An honest maker
backtest MUST model that, or it prints fantasy profit.

Method (no look-ahead, conservative fills):
  1. Per-ticker trajectories from crypto-tight-band-*.jsonl, with bids+asks (cents).
  2. Ground-truth outcome from final yes_mid (>=0.92 YES, <=0.08 NO, else drop).
  3. At the first eligible step (>= MIN_POINTS snapshots), pick the FAVORITE side
     (higher ask = higher implied prob) — same side-selection as the bet-favorite
     baseline, so we isolate the maker-vs-taker effect.
  4. Post a BUY limit at  L = best_bid(side) + JOIN_IMPROVE  (step inside spread).
  5. FILL only if a LATER snapshot's best ask(side) <= L (market traded down to us)
     before close. Unfilled -> no trade (counted separately).
  6. Filled: settle at resolution. correct -> +(100-L)c, wrong -> -L c, minus fee.
     Fee variants: Kalshi 7% taker-style (conservative) and 0c (maker-free).
  7. Compare to the taker bet-favorite baseline on the SAME markets.

Run:  PYTHONIOENCODING=utf-8 python experiments/kalshi_maker_backtest.py
"""

from __future__ import annotations

import glob
import json
import math
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FILES = sorted(glob.glob(str(REPO / "data" / "kalshi" / "crypto-tight-band-*.jsonl")))

RESOLVED_TH = 0.92
MIN_POINTS = 6
JOIN_IMPROVE = 1   # cents inside the spread above the bid


def fee_cents(price_cents: int) -> int:
    p = max(0, min(100, price_cents)) / 100.0
    return math.ceil(0.07 * p * (1 - p) * 100)


def cents(v):
    try:
        return int(round(float(v) * 100))
    except (TypeError, ValueError):
        return None


def load_trajectories():
    """ticker -> chronological list of dicts {ya,na,yb,nb} in cents."""
    rows = defaultdict(list)
    for fp in FILES:
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
                    ya = m.get("yes_ask")
                    na = m.get("no_ask")
                    if ya is None or na is None:
                        continue
                    yb = cents(m.get("yes_bid_dollars"))
                    nb = cents(m.get("no_bid_dollars"))
                    rows[m.get("ticker")].append((ts, {
                        "ya": int(ya), "na": int(na),
                        "yb": yb if yb is not None else max(0, int(ya) - 2),
                        "nb": nb if nb is not None else max(0, int(na) - 2),
                    }))
    series = {}
    for t, pts in rows.items():
        pts.sort(key=lambda x: x[0])
        if len(pts) >= MIN_POINTS:
            series[t] = [d for _, d in pts]
    return series


def outcome_of(traj):
    last = traj[-1]
    ya, na = last["ya"], last["na"]
    s = ya + na
    p = ya / s if s > 0 else 0.5
    if p >= RESOLVED_TH:
        return 1
    if p <= 1 - RESOLVED_TH:
        return 0
    return -1


def main():
    if not FILES:
        print("No crypto-tight-band files found.")
        return
    series = load_trajectories()
    resolved = {t: tr for t, tr in series.items() if outcome_of(tr) != -1}
    print(f"files={len(FILES)}  tickers={len(series)}  resolved={len(resolved)}  "
          f"(maker: post bid+{JOIN_IMPROVE}c, fill iff ask later <= limit)\n")

    maker_fee, maker_free, taker = [], [], []
    eligible = filled = 0

    for t, traj in resolved.items():
        oc = outcome_of(traj)
        e = traj[MIN_POINTS - 1]
        ya, na, yb, nb = e["ya"], e["na"], e["yb"], e["nb"]
        if not (0 < ya < 100 and 0 < na < 100):
            continue
        eligible += 1
        side_yes = ya > na                       # favorite side
        ask0 = ya if side_yes else na
        bid0 = yb if side_yes else nb
        limit = min(ask0 - 1, bid0 + JOIN_IMPROVE)   # inside the spread
        if limit < 1:
            limit = 1
        won = (side_yes and oc == 1) or (not side_yes and oc == 0)

        # taker baseline on the SAME market: buy at ask0 now
        taker.append(((100 - ask0) if won else -ask0) - fee_cents(ask0))

        # maker: filled only if a LATER ask(side) <= limit
        got = False
        for d in traj[MIN_POINTS:]:
            later_ask = d["ya"] if side_yes else d["na"]
            if later_ask <= limit:
                got = True
                break
        if got:
            filled += 1
            gross = (100 - limit) if won else -limit
            maker_fee.append(gross - fee_cents(limit))
            maker_free.append(gross)

    def line(name, arr, denom=None):
        if not arr:
            print(f"  {name:24s} n=0")
            return
        n = len(arr)
        wins = sum(1 for c in arr if c > 0)
        net = sum(arr)
        fr = f"  fill={filled}/{eligible}={filled/eligible*100:.0f}%" if denom else ""
        print(f"  {name:24s} n={n:4d}  win={wins/n*100:5.1f}%  "
              f"net={net:+6d}c (${net/100:+.2f})  avg={net/n:+5.1f}c{fr}")

    print("=== maker vs taker on the same favorite-side markets ===")
    line("taker bet-favorite", taker)
    line("maker (Kalshi 7% fee)", maker_fee, denom=True)
    line("maker (0c fee)", maker_free, denom=True)

    print("\n=== verdict ===")
    if not maker_fee:
        print("  Maker never filled -> no tradeable maker strategy on this data.")
        return
    mnet = sum(maker_fee)
    tnet = sum(taker)
    if mnet > 0 and mnet > tnet:
        print(f"  Maker NET POSITIVE (+{mnet}c) and beats taker baseline ({tnet}c) "
              f"on {filled} fills -> candidate edge. Validate out-of-sample + live "
              f"fill realism before trusting (this fill model is optimistic: real "
              f"queue priority and partial fills will reduce it).")
    elif mnet > 0:
        print(f"  Maker positive (+{mnet}c) but does not beat taker baseline ({tnet}c).")
    else:
        print(f"  Maker NET NEGATIVE ({mnet}c) even with the optimistic fill model "
              f"-> adverse selection: you get filled mostly when the move goes "
              f"against you. No maker edge here either.")


if __name__ == "__main__":
    main()
