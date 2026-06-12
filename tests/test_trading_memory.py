"""Tests for CSF trading memory wiring (Trading Phase 2, issue #323)."""

import os
import sys
import tempfile
import time

import pytest

# Allow importing from src/csf (mirrors tests/test_memory_engine.py)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from csf.memory_engine import MemoryEngine, Tier  # noqa: E402
from csf.trading_memory import (  # noqa: E402
    _extract_tickers,
    query_recent,
    record_order,
    record_signal,
)


SAMPLE_ORDER = {
    "id": "abc12345",
    "symbol": "AAPL",
    "side": "buy",
    "qty": 1.0,
    "type": "market",
    "status": "filled",
    "filled_at": "14:32:01",
    "filled_avg": 123.45,
}

SAMPLE_SIGNAL = {
    "type": "grok",
    "agent": "ROTATION",
    "body": "AAPL bullish breakout, confidence 82%",
    "time": "14:31:55",
}


class TestRecordOrder:
    def test_round_trip_via_query(self):
        with tempfile.TemporaryDirectory() as tmp:
            engine = MemoryEngine(base_path=tmp)
            result = record_order(SAMPLE_ORDER, engine=engine)
            assert result["memory_id"].startswith("trace_")

            records = engine.query(tier=Tier.TRACE, tags=["order"])
            assert len(records) == 1
            rec = records[0]
            assert rec.verify()
            assert rec.content["event"] == "order"
            assert rec.content["symbol"] == "AAPL"
            assert rec.content["id"] == "abc12345"
            assert "trading" in rec.tags
            assert "order" in rec.tags
            assert "filled" in rec.tags
            assert rec.entities == ["AAPL"]
            assert "aapl" in rec.keywords
            assert "buy" in rec.keywords

    def test_confidence_is_high_for_factual_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            engine = MemoryEngine(base_path=tmp)
            record_order(SAMPLE_ORDER, engine=engine)
            rec = engine.query(tier=Tier.TRACE, tags=["order"])[0]
            assert rec.confidence == 1.0


class TestRecordSignal:
    def test_round_trip_via_query(self):
        with tempfile.TemporaryDirectory() as tmp:
            engine = MemoryEngine(base_path=tmp)
            result = record_signal(SAMPLE_SIGNAL, engine=engine)
            assert result["memory_id"].startswith("trace_")

            records = engine.query(tier=Tier.TRACE, tags=["signal"])
            assert len(records) == 1
            rec = records[0]
            assert rec.verify()
            assert rec.content["event"] == "signal"
            assert rec.content["agent"] == "ROTATION"
            assert rec.content["body"] == SAMPLE_SIGNAL["body"]
            assert "trading" in rec.tags
            assert "signal" in rec.tags
            assert "grok" in rec.tags
            # Ticker extracted from the free-text body
            assert "AAPL" in rec.entities
            assert "rotation" in rec.keywords

    def test_signal_confidence_lower_than_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            engine = MemoryEngine(base_path=tmp)
            record_signal(SAMPLE_SIGNAL, engine=engine)
            rec = engine.query(tier=Tier.TRACE, tags=["signal"])[0]
            assert 0 < rec.confidence < 1.0


class TestQueryRecent:
    def test_filters_by_kind_and_sorts_most_recent_first(self):
        with tempfile.TemporaryDirectory() as tmp:
            engine = MemoryEngine(base_path=tmp)

            order_a = dict(SAMPLE_ORDER, id="order-a")
            record_order(order_a, engine=engine)
            time.sleep(0.01)
            record_signal(SAMPLE_SIGNAL, engine=engine)
            time.sleep(0.01)
            order_b = dict(SAMPLE_ORDER, id="order-b")
            record_order(order_b, engine=engine)

            orders = query_recent(limit=10, kind="order", engine=engine)
            assert [o["content"]["id"] for o in orders] == ["order-b", "order-a"]

            signals = query_recent(limit=10, kind="signal", engine=engine)
            assert len(signals) == 1
            assert signals[0]["content"]["event"] == "signal"

            everything = query_recent(limit=10, engine=engine)
            assert len(everything) == 3

    def test_respects_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            engine = MemoryEngine(base_path=tmp)
            for i in range(5):
                record_order(dict(SAMPLE_ORDER, id=f"order-{i}"), engine=engine)
            results = query_recent(limit=2, kind="order", engine=engine)
            assert len(results) == 2


class TestExtractTickers:
    def test_known_ticker_extracted(self):
        assert _extract_tickers("AAPL bullish breakout") == ["AAPL"]

    def test_crypto_pair_extracted(self):
        assert _extract_tickers("BTCUSD breaking out above resistance") == ["BTCUSD"]

    def test_unknown_uppercase_tokens_ignored(self):
        # "RSI" and "VIX" aren't in KNOWN_TICKERS, so they're not treated as entities
        assert _extract_tickers("RSI overbought, VIX elevated") == []

    def test_no_text_returns_empty(self):
        assert _extract_tickers("") == []
        assert _extract_tickers() == []
