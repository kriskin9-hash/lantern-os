import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_paper_trade_ledger_script_blocks_live_and_writes_receipts() -> None:
    text = read("scripts/New-KalshiPaperTradeLedger.ps1")
    required = [
        "Live trading is blocked from this script",
        "paper_position_opened",
        "liveOrderStatus = \"not_submitted\"",
        "realMoneyUsd = 0",
        "kalshi-paper-positions-latest.json",
        "kalshi-paper-ledger.jsonl",
        "kalshi-paper-trade-execution-receipt-2026-05-30.md",
    ]
    missing = [phrase for phrase in required if phrase not in text]
    assert missing == []


def test_paper_positions_are_opened_without_real_money() -> None:
    data = json.loads(read("data/kalshi/kalshi-paper-positions-latest.json"))
    tickets = json.loads(read("data/kalshi/kalshi-paper-trade-tickets-latest.json"))
    assert data["schema"] == "lantern.kalshi.paper_positions.v1"
    assert data["liveTradingStatus"] == "blocked"
    assert data["realMoneyUsd"] == 0
    assert data["positionCount"] == tickets["ticketCount"]
    assert data["allocatedPaperRiskUsd"] <= tickets["budgetPolicy"]["maxDailyPaperLossUsd"]
    for position in data["positions"]:
        assert position["mode"] == "paper_only"
        assert position["status"] == "paper_open"
        assert position["liveOrderStatus"] == "not_submitted"
        assert position["realMoneyUsd"] == 0
        assert position["paperMaxLossUsd"] <= tickets["budgetPolicy"]["maxPerMarketPaperLossUsd"]


def test_paper_trade_execution_receipt_records_no_real_order() -> None:
    text = read("manifests/evidence/kalshi-paper-trade-execution-receipt-2026-05-30.md")
    required = [
        "Kalshi Paper Trade Execution Receipt",
        "paper positions opened locally",
        "No authenticated Kalshi request was made",
        "No real order was submitted",
        "Paper positions opened",
        "Real money spent",
        "$0.00",
        "data/kalshi/kalshi-paper-positions-latest.json",
        "data/kalshi/kalshi-paper-ledger.jsonl",
    ]
    missing = [phrase for phrase in required if phrase not in text]
    assert missing == []
