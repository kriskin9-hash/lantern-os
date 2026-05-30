import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_near_term_paper_pl_resolver_is_public_data_only() -> None:
    text = read("scripts/Resolve-KalshiNearTermPaperBlock.ps1")
    required = [
        "lantern.kalshi.near_term_paper_pl.v1",
        "external-api.kalshi.com/trade-api/v2/markets/$Ticker",
        "Paper P/L only",
        "No authenticated Kalshi request was made",
        "No real order was submitted",
        "totalPaperPnlUsd",
    ]
    missing = [phrase for phrase in required if phrase not in text]
    assert missing == []


def test_near_term_paper_pl_json_if_present_is_blocked() -> None:
    path = ROOT / "data/kalshi/kalshi-near-term-paper-block-pl-latest.json"
    if not path.exists():
        return
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["schema"] == "lantern.kalshi.near_term_paper_pl.v1"
    assert data["liveTradingStatus"] == "blocked"
    assert data["realMoneyUsd"] == 0
    assert data["paperOrderCount"] == len(data["orders"])
    assert "totalPaperPnlUsd" in data
    for order in data["orders"]:
        assert order["paperOutcome"] in {"paper_win", "paper_loss", "unsettled", "unknown"}
