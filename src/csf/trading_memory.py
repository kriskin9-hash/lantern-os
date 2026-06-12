"""
CSF Memory: trading orders & agent signals (Trading Phase 2, issue #323).

Persists trading orders and agent signals into the existing CSF
MemoryEngine (src/csf/memory_engine.py) as Tier.TRACE records, tagged
"trading" + "order"/"signal", so dream-chat and other LanternOS agents can
query recent trading activity (e.g. "what happened with AAPL today?").

This module is the **Python-native reference implementation** of that CSF
record shape (Tier.TRACE, PrivacyScope.INTERNAL, CubePartition.RAW, tags
"trading" + "order"/"signal" + status/type) and is exercised by
tests/test_trading_memory.py.

LanternOS's Node runtime does **not** call this module — it has its own
pure-JS implementation with the same record shape and the same
data/csf_memory/raw.jsonl registry format:
apps/lantern-garage/lib/csf-memory-writer.js (writes) and
apps/lantern-garage/lib/trading-memory.js (orders/signals API + local
trading store). That keeps the trading-memory feature local-first — no
Python process is spawned at runtime, and no external service is required.
Records written by either side land in the same registry and are
queryable by both MemoryEngine.query() and the JS queryRecent().

Scope: orders + signals only (per #323) — not a general trading->CSF
pipeline. Each record_*() call writes ONE trace record per invocation;
callers are responsible for de-duplicating against already-seen order ids /
signal entries so that repeated ingestion does not produce a
duplicate-write storm (see apps/lantern-garage/lib/trading-memory.js's
seen-set).

Optional CLI, useful for manual inspection/debugging (not used by any
runtime code path):

    python -m csf.trading_memory --action record-order  --data '<json order>'
    python -m csf.trading_memory --action record-signal --data '<json signal>'
    python -m csf.trading_memory --action query --kind order|signal --limit 20

Each action prints a single JSON object/array to stdout.
"""

from __future__ import annotations

import json
import re
import sys
from typing import Any, Dict, List, Optional

from .memory_engine import MemoryEngine, MemoryRecord, PrivacyScope, Tier, create_trace

# Tickers the AI Trader watches by default (agents.py DEFAULT_WATCHLIST) plus
# common index/ETF tickers. Used to disambiguate real tickers from other
# all-caps tokens (agent names, "RSI", "VIX", etc.) when scanning agent-log
# free text for entities. This is a best-effort heuristic, not exhaustive.
KNOWN_TICKERS = {
    "AAPL", "AMZN", "INTC", "AMD", "SHOP", "SPY", "TSLA", "NVDA", "ASML",
    "META", "MSFT", "JPM", "GLD", "QQQ", "VIXY",
}

# Generic crypto pairs (BTCUSD, ETHUSD, SOLUSD, ...) and any 2-5 letter
# all-caps token immediately followed by "USD".
_CRYPTO_RE = re.compile(r"\b[A-Z]{2,5}USD\b")
_TOKEN_RE = re.compile(r"\b[A-Z]{1,5}\b")


def _extract_tickers(*texts: str, limit: int = 5) -> List[str]:
    """Best-effort extraction of ticker symbols from free-text agent log bodies."""
    found: List[str] = []
    for text in texts:
        if not text:
            continue
        for m in _CRYPTO_RE.findall(text):
            if m not in found:
                found.append(m)
        for m in _TOKEN_RE.findall(text):
            if m in KNOWN_TICKERS and m not in found:
                found.append(m)
        if len(found) >= limit:
            break
    return found[:limit]


def record_order(order: Dict[str, Any], engine: Optional[MemoryEngine] = None) -> Dict[str, Any]:
    """Write a single AI Trader order (from /api/orders) as a CSF trace record."""
    engine = engine or MemoryEngine()

    symbol = str(order.get("symbol") or "").upper()
    side = str(order.get("side") or "").lower()
    status = str(order.get("status") or "").lower()
    qty = order.get("qty")
    order_id = order.get("id", "")

    summary = f"Order {order_id}: {side} {qty} {symbol} ({status})".strip()

    tags = ["trading", "order"]
    if status:
        tags.append(status)

    keywords = [k for k in [symbol.lower(), side, status, "order"] if k]
    entities = [symbol] if symbol else []

    record = create_trace(
        text=summary,
        session_id="trading",
        surface="trading",
        role="system",
        confidence=1.0,
        privacy_scope=PrivacyScope.INTERNAL,
        tags=tags,
        keywords=keywords,
        entities=entities,
    )
    record.content.update({"event": "order", **order})

    path = engine.write(record)
    return {"memory_id": record.memory_id, "path": str(path)}


def record_signal(entry: Dict[str, Any], engine: Optional[MemoryEngine] = None) -> Dict[str, Any]:
    """Write a single AI Trader agent-log entry (from /api/agent-log) as a CSF trace record."""
    engine = engine or MemoryEngine()

    agent = str(entry.get("agent") or "")
    entry_type = str(entry.get("type") or "")
    body = str(entry.get("body") or "")

    tags = ["trading", "signal"]
    if entry_type:
        tags.append(entry_type.lower())

    keywords = [k for k in [agent.lower(), entry_type.lower(), "signal"] if k]
    entities = _extract_tickers(body, agent)

    record = create_trace(
        text=body or f"{agent}: (no message)",
        session_id="trading",
        surface="trading",
        role="agent",
        confidence=0.6,
        privacy_scope=PrivacyScope.INTERNAL,
        tags=tags,
        keywords=keywords,
        entities=entities,
    )
    record.content.update({"event": "signal", **entry})

    path = engine.write(record)
    return {"memory_id": record.memory_id, "path": str(path)}


def query_recent(limit: int = 20, kind: Optional[str] = None, engine: Optional[MemoryEngine] = None) -> List[Dict[str, Any]]:
    """Return the most recent trading trace records (orders and/or signals).

    `kind`, if given, should be "order" or "signal" — filters to records
    carrying that tag. MemoryEngine.query()'s tags filter is OR-based and
    its full-scan path short-circuits at `limit` in registry order (oldest
    first), so we over-fetch with a high limit and re-sort/filter here to
    get true "most recent N" semantics.
    """
    engine = engine or MemoryEngine()
    records = engine.query(tags=["trading"], tier=Tier.TRACE, limit=10000)
    if kind:
        records = [r for r in records if kind in r.tags]
    records.sort(key=lambda r: r.created_at, reverse=True)
    return [r.to_dict() for r in records[:limit]]


def _main(argv: Optional[List[str]] = None) -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--action", choices=["record-order", "record-signal", "query"], required=True)
    parser.add_argument("--data", default=None, help="JSON payload for record-order / record-signal")
    parser.add_argument("--kind", default=None, choices=["order", "signal"], help="Filter for --action query")
    parser.add_argument("--limit", type=int, default=20, help="Max records for --action query")
    args = parser.parse_args(argv)

    if args.action == "record-order":
        payload = json.loads(args.data) if args.data else {}
        result = record_order(payload)
    elif args.action == "record-signal":
        payload = json.loads(args.data) if args.data else {}
        result = record_signal(payload)
    else:  # query
        result = query_recent(limit=args.limit, kind=args.kind)

    json.dump(result, sys.stdout, ensure_ascii=False, default=str)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(_main())
