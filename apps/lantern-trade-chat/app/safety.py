"""Trading safety rails: kill switch, risk caps, and the live-order ledger.

Mirrors the gates enforced by scripts/Invoke-KalshiLiveOrder.ps1 and the policy
in skills/trade/SKILL.md: dry-run by default, kill switch, per-order cap,
per-day loss cap, and a max trades-per-day limit. The public web surface never
weakens these; it only adds OAuth on top.
"""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from .config import Settings


@dataclass
class OrderPlan:
    ticker: str
    side: str          # "yes" | "no"
    action: str        # "buy" | "sell"
    count: int
    limit_cents: int
    order_type: str = "limit"

    @property
    def cost_usd(self) -> float:
        # Max cash at risk for a limit buy = count * price. Used for caps.
        return round(self.count * self.limit_cents / 100.0, 2)


def kill_switch_active(settings: Settings) -> bool:
    if settings.kill_switch_path.exists():
        return True
    return (os.environ.get("KALSHI_KILL_SWITCH", "").strip().lower() in {"1", "true", "yes", "on"})


def today_summary(settings: Settings) -> tuple[int, float]:
    """Return (live_trades_today, live_risk_usd_today) from the ledger."""
    path = settings.ledger_path
    if not path.exists():
        return 0, 0.0
    today = datetime.now(timezone.utc).date().isoformat()
    trades = 0
    risk = 0.0
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if entry.get("event") != "live_order_submitted":
            continue
        ts = str(entry.get("timestamp", ""))
        if not ts.startswith(today):
            continue
        trades += 1
        risk += float(entry.get("costUsd", 0.0) or 0.0)
    return trades, round(risk, 2)


def evaluate_gates(settings: Settings, plan: OrderPlan, balance_usd: float | None) -> list[str]:
    """Return a list of human-readable blockers. Empty list => order may proceed."""
    blockers: list[str] = []
    if not settings.live_enabled:
        blockers.append("Live trading is disabled (set LANTERN_LIVE_ENABLED=1 to arm this deployment).")
    if kill_switch_active(settings):
        blockers.append("Kill switch is active — live orders are blocked.")
    if not settings.has_credentials:
        blockers.append("No Kalshi credentials configured (KALSHI_API_KEY_ID / KALSHI_PRIVATE_KEY).")

    if plan.cost_usd > settings.max_per_order_usd:
        blockers.append(
            f"Per-order cap exceeded: ${plan.cost_usd:.2f} > ${settings.max_per_order_usd:.2f}."
        )
    if balance_usd is not None and plan.cost_usd > balance_usd:
        blockers.append(f"Insufficient balance: order ${plan.cost_usd:.2f} > balance ${balance_usd:.2f}.")

    trades_today, risk_today = today_summary(settings)
    if trades_today >= settings.max_trades_per_day:
        blockers.append(
            f"Daily trade limit reached: {trades_today} >= {settings.max_trades_per_day}."
        )
    if risk_today + plan.cost_usd > settings.max_daily_loss_usd:
        blockers.append(
            f"Daily risk cap exceeded: ${risk_today + plan.cost_usd:.2f} > ${settings.max_daily_loss_usd:.2f}."
        )
    return blockers


def append_ledger(settings: Settings, event: str, plan: OrderPlan, actor: str, extra: dict | None = None) -> None:
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "actor": actor,
        "environment": settings.environment,
        "costUsd": plan.cost_usd,
        **asdict(plan),
    }
    if extra:
        entry.update(extra)
    path: Path = settings.ledger_path
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")
