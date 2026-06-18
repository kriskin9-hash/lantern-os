"""
Kalshi realized-PnL backtest (#693) — does the live momentum signal have an
edge AFTER fees, or is the account just bleeding?

Honest method (no look-ahead):
  1. Rebuild per-ticker trajectories from the crypto tight-band capture
     (data/kalshi/crypto-tight-band-*.jsonl): chronological (yes_ask, no_ask) cents.
  2. Ground-truth outcome from the FINAL snapshot: yes_mid >= RESOLVED_TH -> YES,
     <= 1-RESOLVED_TH -> NO, else unresolved (dropped — can't score honestly).
  3. Walk each trajectory forward. At the first step with >= MIN_POINTS snapshots,
     run the SAME CIOConvergenceModel the live trader uses, on data SEEN SO FAR
     only. If it fires with |edge| > EDGE, enter: buy favSide at that step's ask.
  4. Settle at resolution: correct -> +(100 - entry_ask)c, wrong -> -entry_ask c.
     Subtract Kalshi trade fee = ceil(0.07 * P * (1-P) * 100) cents (P in dollars).
  5. Compare the signal to honest baselines on the SAME resolved markets:
       - bet-favorite : always buy the side currently priced > 50c
       - always-trade : momentum side every market (no gate)
       - random       : seed-fixed coin flip
     A strategy with no positive NET (after-fee) PnL vs these has no edge.

Run:  PYTHONIOENCODING=utf-8 python experiments/kalshi_pnl_backtest.py
"""

from __future__ import annotations

import glob
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kalshi_cio_backtest import Snapshot, MarketTrajectory, CIOConvergenceModel  # noqa

REPO = Path(__file__).resolve().parents[1]
FILES = sorted(glob.glob(str(REPO / "data" / "kalshi" / "crypto-tight-band-*.jsonl")))

RESOLVED_TH = 0.92   # final yes_mid >= this => YES resolved
MIN_POINTS = 6
EDGE = 0.08          # live trader's default --edge
SEED = 12345


def kalshi_fee_cents(price_cents: int) -> int:
    """Kalshi trading fee: ceil(0.07 * C * P * (1-P)) per contract, P in dollars."""
    p = max(0, min(100, price_cents)) / 100.0
    return math.ceil(0.07 * p * (1 - p) * 100)


def load_trajectories():
    """ticker -> chronological list of (yes_ask_c, no_ask_c)."""
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
                    ya, na = m.get("yes_ask"), m.get("no_ask")
                    if ya is None or na is None:
                        continue
                    rows[m.get("ticker")].append((ts, int(ya), int(na)))
    series = {}
    for t, pts in rows.items():
        pts.sort(key=lambda x: x[0])
        if len(pts) >= MIN_POINTS:
            series[t] = [(ya, na) for _, ya, na in pts]
    return series


def outcome_of(traj):
    ya, na = traj[-1]
    s = ya + na
    p = ya / s if s > 0 else 0.5
    if p >= RESOLVED_TH:
        return 1
    if p <= 1 - RESOLVED_TH:
        return 0
    return -1


def settle(side_yes: bool, entry_ask: int, outcome: int):
    """Net cents for a 1-contract buy held to resolution, after fee."""
    won = (side_yes and outcome == 1) or (not side_yes and outcome == 0)
    gross = (100 - entry_ask) if won else -entry_ask
    return gross - kalshi_fee_cents(entry_ask), won


def summarize(name, trades):
    if not trades:
        print(f"  {name:16s} n=0   (no trades)")
        return 0, 0.0
    n = len(trades)
    wins = sum(1 for _, w in trades if w)
    net = sum(c for c, _ in trades)
    print(f"  {name:16s} n={n:4d}  win={wins/n*100:5.1f}%  "
          f"net={net:+6d}c (${net/100:+.2f})  avg={net/n:+5.1f}c/trade")
    return net, wins / n


def main():
    if not FILES:
        print("No crypto-tight-band files found.")
        return
    series = load_trajectories()
    resolved = {t: tr for t, tr in series.items() if outcome_of(tr) != -1}
    print(f"files={len(FILES)}  tickers={len(series)}  resolved={len(resolved)} "
          f"(EDGE={EDGE}, fee=Kalshi 7%)\n")

    model = CIOConvergenceModel()
    rng_state = SEED
    def coin():
        nonlocal rng_state
        rng_state = (rng_state * 1103515245 + 12345) & 0x7fffffff
        return rng_state & 1

    sig, fav, always, rand = [], [], [], []

    for t, traj in resolved.items():
        oc = outcome_of(traj)
        # walk forward; enter on FIRST momentum signal (no look-ahead)
        entered = False
        for i in range(MIN_POINTS, len(traj)):
            seen = traj[:i]
            snaps = [Snapshot(ya / 100.0, na / 100.0) for ya, na in seen]
            p_star, has = model.predict(MarketTrajectory(snaps, outcome=-1))
            price_now = snaps[-1].yes_mid
            edge = p_star - price_now
            if has and abs(edge) > EDGE:
                side_yes = edge > 0
                ya, na = seen[-1]
                entry = ya if side_yes else na
                if 0 < entry < 100:
                    sig.append(settle(side_yes, entry, oc))
                entered = True
                break
        # baselines entered at first eligible step (i = MIN_POINTS) for fairness
        ya0, na0 = traj[MIN_POINTS - 1]
        if 0 < ya0 < 100 and 0 < na0 < 100:
            fav_yes = ya0 > na0
            fav.append(settle(fav_yes, ya0 if fav_yes else na0, oc))
            # always-trade momentum: sign of last move over first window
            mom_yes = traj[MIN_POINTS - 1][0] >= traj[0][0]
            always.append(settle(mom_yes, ya0 if mom_yes else na0, oc))
            r_yes = bool(coin())
            rand.append(settle(r_yes, ya0 if r_yes else na0, oc))

    print("=== realized PnL (1 contract/market, held to resolution, after fees) ===")
    sig_net, _ = summarize("momentum-signal", sig)
    fav_net, _ = summarize("bet-favorite", fav)
    always_net, _ = summarize("always-momentum", always)
    rand_net, _ = summarize("random", rand)

    print("\n=== verdict ===")
    best_base = max(fav_net, always_net, rand_net)
    if not sig:
        print("  Signal never fired on resolved markets — no tradeable edge to measure.")
    elif sig_net > 0 and sig_net > best_base:
        print(f"  Signal NET POSITIVE (+{sig_net}c) and beats best baseline ({best_base}c) "
              f"-> candidate edge. Validate out-of-sample before trusting.")
    elif sig_net > 0:
        print(f"  Signal positive (+{sig_net}c) but does NOT beat bet-favorite/baseline "
              f"({best_base}c) -> no edge beyond buying the favorite.")
    else:
        print(f"  Signal NET NEGATIVE ({sig_net}c) -> no edge; it loses money after fees. "
              f"This matches the live account drawdown.")


if __name__ == "__main__":
    main()
