"""
Crypto + S&P 500 tight-band observer.

Polls Kalshi KXBTC / KXETH / KXDOGE / KXINX series every POLL_INTERVAL seconds
and writes snapshots to data/kalshi/crypto-tight-band-YYYY-MM-DD.jsonl in the
same format as the sports tight-band observer, so kalshi_tightband_analysis.py
can run on it without changes.

Run:
    python experiments/crypto_tightband_observer.py [--interval 30] [--hours 8]

Typical usage:
    - Start before a day-session market opens (e.g. 09:30 ET for KXINX)
    - Let it run until the market resolves
    - Run: python experiments/kalshi_tightband_analysis.py data/kalshi/crypto-tight-band-YYYY-MM-DD.jsonl
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import urllib.request
import urllib.parse

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

KALSHI_HOST = "external-api.kalshi.com"
BASE = "/trade-api/v2"

# Kalshi series → friendly symbol name
SERIES = {
    "KXBTC":  "BTC",
    "KXETH":  "ETH",
    "KXDOGE": "DOGE",
    "KXINX":  "SPX",
}

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "kalshi"


def kalshi_get(endpoint: str, params: dict = None) -> dict:
    url = f"https://{KALSHI_HOST}{BASE}{endpoint}"
    if params:
        url += "?" + urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode())


def fetch_series_markets(series_ticker: str) -> list[dict]:
    """Return all open markets for a series (cents-normalised)."""
    data = kalshi_get("/markets", {"status": "open", "limit": 50, "series_ticker": series_ticker})
    markets = data.get("markets") or []
    for m in markets:
        # Normalise prices to cents (int) if they came back as dollars
        for field_d, field_c in [("yes_ask_dollars", "yes_ask"), ("no_ask_dollars", "no_ask")]:
            if field_c not in m or m[field_c] is None:
                if field_d in m and m[field_d] is not None:
                    m[field_c] = round(float(m[field_d]) * 100)
                else:
                    m[field_c] = 0
    return markets


def pick_best_market(markets: list[dict]) -> dict | None:
    """Pick the most liquid market that hasn't converged yet."""
    now_ms = time.time() * 1000
    active = [
        m for m in markets
        if m.get("close_time") and
           datetime.fromisoformat(m["close_time"].replace("Z", "+00:00")).timestamp() * 1000 > now_ms
        and (m.get("yes_ask") or 0) >= 5
        and (m.get("yes_ask") or 0) <= 95
    ]
    pool = active or [m for m in markets if m.get("close_time") and
                      datetime.fromisoformat(m["close_time"].replace("Z", "+00:00")).timestamp() * 1000 > now_ms]
    if not pool:
        return None
    return max(pool, key=lambda m: float(m.get("open_interest_fp") or m.get("open_interest") or 0))


def snapshot(tracked_tickers: dict[str, str]) -> tuple[list[dict], int]:
    """
    Poll all series and return (markets_list, resolved_count).
    tracked_tickers: ticker → series_ticker mapping accumulated across the run.
    """
    markets_out = []
    resolved = 0
    now_ms = time.time() * 1000

    for series, symbol in SERIES.items():
        try:
            all_markets = fetch_series_markets(series)
        except Exception as e:
            print(f"  [{symbol}] fetch error: {e}", flush=True)
            continue

        best = pick_best_market(all_markets)
        if best is None:
            # include already-resolved markets to record their final state
            expired = [m for m in all_markets if m.get("result") not in (None, "")]
            if expired:
                best = expired[-1]
                resolved += 1
            else:
                print(f"  [{symbol}] no active markets", flush=True)
                continue

        ya = best.get("yes_ask") or 0
        na = best.get("no_ask") or 0
        print(f"  [{symbol}] {best['ticker']}  yes={ya}¢ no={na}¢  close={best.get('close_time','?')[:16]}", flush=True)
        markets_out.append(best)

    return markets_out, resolved


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--interval", type=int, default=30, help="Poll interval seconds (default 30)")
    ap.add_argument("--hours", type=float, default=8, help="Run for this many hours (default 8)")
    args = ap.parse_args()

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out_path = DATA_DIR / f"crypto-tight-band-{today}.jsonl"
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    total_secs = int(args.hours * 3600)
    n_polls = total_secs // args.interval
    print(f"Crypto tight-band observer  →  {out_path.name}", flush=True)
    print(f"Interval: {args.interval}s  |  Duration: {args.hours}h  ({n_polls} polls)", flush=True)
    print("Series: KXBTC BTC  |  KXETH ETH  |  KXDOGE DOGE  |  KXINX SPX", flush=True)
    print("-" * 60, flush=True)

    tracked: dict[str, str] = {}
    n = 0
    start_t = time.time()

    while time.time() - start_t < total_secs:
        ts = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        print(f"\n[{ts[:19]}] poll {n + 1}/{n_polls}", flush=True)

        markets, resolved_count = snapshot(tracked)

        row = {
            "ts": ts,
            "markets": len(markets),
            "exitCount": resolved_count,
            "snapshot": {"markets": markets},
        }
        with out_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")

        n += 1
        if n >= n_polls:
            break

        elapsed = time.time() - start_t
        sleep_for = max(0, args.interval * n - elapsed)
        if sleep_for > 0:
            time.sleep(sleep_for)

    print(f"\nDone. Wrote {n} snapshots to {out_path}", flush=True)
    print(f"Analyse: python experiments/kalshi_tightband_analysis.py {out_path}", flush=True)


if __name__ == "__main__":
    main()
