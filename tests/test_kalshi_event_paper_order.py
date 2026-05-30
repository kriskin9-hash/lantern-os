import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_event_paper_order_script_blocks_live_and_uses_public_event() -> None:
    text = read("scripts/New-KalshiEventPaperOrder.ps1")
    required = [
        "KXMLBGAME-26MAY311435KCTEX",
        "with_nested_markets=true",
        "Live trading is blocked from this script",
        "paper_buy_limit_maker",
        "paper_open_unfilled",
        "Buying both sides at the ask would cross the spread",
    ]
    missing = [phrase for phrase in required if phrase not in text]
    assert missing == []


def test_selected_event_paper_orders_are_not_real_orders() -> None:
    data = json.loads(read("data/kalshi/kalshi-selected-event-paper-orders-latest.json"))
    assert data["schema"] == "lantern.kalshi.event_paper_orders.v1"
    assert data["eventTicker"] == "KXMLBGAME-26MAY311435KCTEX"
    assert data["liveTradingStatus"] == "blocked"
    assert data["realMoneyUsd"] == 0
    assert data["budgetPolicy"]["bankrollUsd"] == 50.0
    assert data["budgetPolicy"]["allocatedPaperRiskUsd"] <= data["budgetPolicy"]["maxDailyPaperLossUsd"]
    assert data["paperOrderCount"] >= 1
    for order in data["orders"]:
        assert order["action"] == "paper_buy_limit_maker"
        assert order["orderStatus"] == "paper_open_unfilled"
        assert order["liveOrderStatus"] == "not_submitted"
        assert order["realMoneyUsd"] == 0
        assert order["paperMaxLossUsd"] <= data["budgetPolicy"]["maxPerOrderPaperLossUsd"]
        assert order["outcomeConfidence"] == "not_estimated"


def test_selected_event_receipt_names_kc_texas_and_boundary() -> None:
    text = read("manifests/evidence/kalshi-selected-event-paper-order-receipt-2026-05-30.md")
    required = [
        "Kalshi Selected Event Paper Order Receipt",
        "Kansas City vs Texas",
        "KXMLBGAME-26MAY311435KCTEX",
        "No authenticated Kalshi request was made",
        "No real order was submitted",
        "paper_open_unfilled",
        "data/kalshi/kalshi-selected-event-paper-orders-latest.json",
    ]
    missing = [phrase for phrase in required if phrase not in text]
    assert missing == []
