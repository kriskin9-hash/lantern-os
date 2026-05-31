"""Tiny, deterministic natural-language parser for trading chat.

No LLM dependency: turns messages like
    "buy 1 yes on KXBTC at 40c"
    "dry run sell 2 no FED-25 limit 12"
    "balance"  /  "help"
into a structured intent. Keeping it rule-based means the order path is
auditable and never hallucinates a trade.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from .safety import OrderPlan


@dataclass
class Intent:
    kind: str                      # "order" | "balance" | "help" | "unknown"
    plan: OrderPlan | None = None
    live: bool = False             # explicit live request ("live ...")
    message: str = ""


_ORDER_RE = re.compile(
    r"\b(?P<action>buy|sell)\b"
    r"(?:\s+(?P<count>\d+))?"
    r"\s+(?P<side>yes|no)\b"
    r"(?:\s+on)?\s+(?P<ticker>[A-Za-z0-9._\-]+)"
    r"(?:\s+(?:at|limit|@)\s*(?P<limit>\d+)\s*(?:c|¢|cents)?)?",
    re.IGNORECASE,
)


def parse(text: str) -> Intent:
    raw = (text or "").strip()
    low = raw.lower()
    if not raw:
        return Intent(kind="unknown", message="Say something like: buy 1 yes on TICKER at 40c")
    if low in {"help", "?", "/help"}:
        return Intent(kind="help")
    if "balance" in low or low in {"bal", "/balance"}:
        return Intent(kind="balance")

    live = bool(re.search(r"\blive\b", low)) and not re.search(r"\bdry[\s-]?run\b", low)

    match = _ORDER_RE.search(raw)
    if not match:
        return Intent(
            kind="unknown",
            message="Couldn't parse an order. Try: buy 1 yes on TICKER at 40c (add 'live' to place real money).",
        )
    count = int(match.group("count") or 1)
    limit = int(match.group("limit") or 0)
    if limit <= 0 or limit > 99:
        return Intent(
            kind="unknown",
            message="Limit price must be between 1 and 99 cents. Example: buy 1 yes on TICKER at 40c",
        )
    plan = OrderPlan(
        ticker=match.group("ticker").upper(),
        side=match.group("side").lower(),
        action=match.group("action").lower(),
        count=count,
        limit_cents=limit,
    )
    return Intent(kind="order", plan=plan, live=live)
