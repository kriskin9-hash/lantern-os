"""
Tests for experiments/kalshi_council_train.py — the Kalshi arm of the Σ₀ council.

Pins two things that must not silently drift:
  1. The fee / EV math is parity with apps/lantern-garage/lib/kalshi-fees.js (the
     external-reality anchor — if these disagree, the council grades against a
     different fee model than the gate the UI shows).
  2. Every emitted council row carries the schema sigma0-trader-council.js reads.
"""

import json
import sys
from pathlib import Path

import pytest

EXPERIMENTS = Path(__file__).resolve().parents[1] / "experiments"
sys.path.insert(0, str(EXPERIMENTS))

ct = pytest.importorskip("kalshi_council_train")
from kalshi_cio_backtest import CIOConvergenceModel  # noqa: E402


# ── fee / EV parity with kalshi-fees.js ─────────────────────────────────────────
def test_fee_fraction_peaks_at_50c():
    # kalshi-fees.js: per-contract fee peaks at P=0.50 -> 0.07*0.25 = 0.0175
    assert ct.fee_fraction(50) == pytest.approx(0.0175, abs=1e-6)
    # symmetric and smaller away from the middle
    assert ct.fee_fraction(20) == pytest.approx(0.07 * 0.2 * 0.8, abs=1e-9)
    assert ct.fee_fraction(80) == pytest.approx(ct.fee_fraction(20), abs=1e-9)


def test_breakeven_50c_is_about_5175pct():
    # buying a 50c contract needs ~51.75% win to break even after fee
    assert ct.breakeven_win_prob(50) == pytest.approx(0.5175, abs=1e-4)


def test_net_ev_sign_matches_breakeven():
    # exactly at market price -> negative EV (you only paid the fee)
    assert ct.net_ev_cents(50, 0.50) < 0
    # well above breakeven -> positive
    assert ct.net_ev_cents(50, 0.70) > 0
    # is_positive_ev agrees with breakeven_win_prob
    assert ct.is_positive_ev(50, 0.52) is True
    assert ct.is_positive_ev(50, 0.51) is False


def test_p_win_model_monotone_and_clamped():
    # pulls market price toward 1.0; always >= market price; clamped to [0.05, 0.95]
    assert ct.p_win_model(0.50) > 0.50
    assert ct.p_win_model(0.10) < ct.p_win_model(0.90)
    assert 0.05 <= ct.p_win_model(0.001) <= 0.95
    assert 0.05 <= ct.p_win_model(0.999) <= 0.95


# ── signal extraction + row schema ──────────────────────────────────────────────
def _uptrend_pts(n=60):
    """A clean YES-trending market: yes_ask climbs 20c -> 85c."""
    pts = []
    for i in range(n):
        ya = min(95, 20 + i)        # rising
        na = max(5, 100 - ya)       # mirror
        pts.append((f"2026-06-30T00:{i:02d}:00Z", ya, na))
    return pts


def test_first_entry_picks_the_trend_side_with_signal_vector():
    model = CIOConvergenceModel()
    e = ct.first_entry(_uptrend_pts(), "2026-06-30T01:00:00Z", model)
    assert e is not None, "momentum signal should fire on a clean uptrend"
    assert e["side_yes"] is True
    assert 0 < e["entry"] < 100
    # the per-signal-edge vector the council reads
    assert set(e["signals"]) == {"momentum", "convergence", "time_band", "spread"}
    for v in e["signals"].values():
        assert 0.0 <= v <= 1.0


COUNCIL_KEYS = {
    "record_id", "ticker", "side", "confidence", "passed", "outcome",
    "brier_score", "pnl_pct", "signals", "source", "conviction_recorded", "graded_at",
}


def test_emitted_row_has_council_schema(tmp_path, monkeypatch):
    """Run the trainer on a tiny synthetic capture and check the emitted JSONL rows."""
    # one resolved YES market written in the tight-band capture format
    cap = tmp_path / "crypto-tight-band-2026-06-30.jsonl"
    with cap.open("w", encoding="utf-8") as fh:
        for i in range(60):
            ya = min(97, 38 + i)       # climbs to 97c so final yes_mid >= RESOLVED_TH -> YES
            na = max(3, 100 - ya)
            row = {"ts": f"2026-06-30T00:{i:02d}:00Z",
                   "snapshot": {"markets": [{"ticker": "KXBTC15M-TEST",
                                             "yes_ask": ya, "no_ask": na,
                                             "title": "BTC up?", "close_time": "2026-06-30T01:00:00Z"}]}}
            fh.write(json.dumps(row) + "\n")

    # redirect every output path into tmp so we don't touch real data
    monkeypatch.setattr(ct, "KALSHI_DIR", tmp_path)
    monkeypatch.setattr(ct, "COUNCIL_OUTCOMES", tmp_path / "council-outcomes.jsonl")
    monkeypatch.setattr(ct, "SEARCH_REPORT", tmp_path / "report.json")
    monkeypatch.setattr(ct, "REPLAY_OUTCOMES", tmp_path / "replay-outcomes.json")
    monkeypatch.setattr(ct, "REPLAY_DECK", tmp_path / "replay-deck.json")
    monkeypatch.setattr(sys, "argv", ["kalshi_council_train.py"])

    ct.main()

    rows = [json.loads(l) for l in (tmp_path / "council-outcomes.jsonl").read_text().splitlines() if l.strip()]
    assert rows, "trainer should emit at least one council row"
    for r in rows:
        assert COUNCIL_KEYS.issubset(r), f"missing keys: {COUNCIL_KEYS - set(r)}"
        assert r["source"] == "kalshi-backtest"
        assert r["conviction_recorded"] is True
        assert r["outcome"] in (0, 1)
        assert 0.0 <= r["confidence"] <= 1.0
        assert r["brier_score"] == pytest.approx((r["confidence"] - r["outcome"]) ** 2, abs=1e-3)

    report = json.loads((tmp_path / "report.json").read_text())
    assert "verdict" in report and report["sweep"]
    outcomes = json.loads((tmp_path / "replay-outcomes.json").read_text())
    assert "KXBTC15M-TEST" in outcomes and outcomes["KXBTC15M-TEST"]["outcome"] == 1
