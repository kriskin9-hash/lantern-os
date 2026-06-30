"""
Tests for src/trading_agents/convergence_ev.py — the Σ₀ expected-value decision
layer that replaces Riley's WAIT/GOOD/PERFECT tiers with a transparent EV gate.

Pins the contract: (a) confirming evidence raises p_win monotonically, (b) the
EV gate only fires on a real positive edge, (c) news is signed to direction, and
(d) every decision carries an auditable convergence record + `why`.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "trading_agents"))

from convergence_ev import score_convergence, EV_MIN, P_MIN


def _ev(**kw):
    base = dict(direction="BULLISH", llm_conf=50, backtest_winrate=0.5, target_r=2.0)
    base.update(kw)
    return score_convergence(base)


def test_strong_setup_enters_with_high_pwin():
    r = _ev(llm_conf=72, in_zone=True, zone_strength=85, zone_touches=3,
            structure_shifted=True, structure_conf=75, pattern_grade="A",
            trend_aligned=True, news_sentiment=0.4)
    assert r["decision"] == "ENTER"
    assert r["p_win"] > 0.7
    assert r["ev_r"] >= EV_MIN


def test_no_confirmation_skips():
    # No grounding signal at all → SKIP via the evidence floor, even if a 2:1
    # target would otherwise make a coin-flip look +EV.
    r = _ev(llm_conf=52, in_zone=False, structure_shifted=False,
            pattern_grade=None, trend_aligned=False, news_sentiment=0.0)
    assert r["decision"] == "SKIP"


def test_confirming_evidence_is_monotonic():
    weak = _ev(in_zone=False, structure_shifted=False, pattern_grade=None)["p_win"]
    mid = _ev(in_zone=True, zone_strength=70, structure_shifted=False, pattern_grade="B")["p_win"]
    strong = _ev(in_zone=True, zone_strength=90, zone_touches=3,
                 structure_shifted=True, pattern_grade="A", trend_aligned=True)["p_win"]
    assert weak < mid < strong


def test_news_is_signed_to_direction():
    # Bullish news helps a long, hurts a short — same |sentiment|.
    long_p = _ev(direction="BULLISH", news_sentiment=0.8)["signals"]["news"]
    short_p = score_convergence(dict(direction="BEARISH", llm_conf=50,
                                     backtest_winrate=0.5, target_r=2.0,
                                     news_sentiment=0.8))["signals"]["news"]
    assert long_p > 0.5 > short_p


def test_higher_target_can_rescue_a_coinflip():
    low_t = _ev(llm_conf=58, in_zone=True, zone_strength=60, target_r=1.2)
    high_t = _ev(llm_conf=58, in_zone=True, zone_strength=60, target_r=3.0)
    assert high_t["ev_r"] > low_t["ev_r"]


def test_every_decision_carries_an_auditable_record():
    r = _ev(in_zone=True, zone_strength=80, structure_shifted=True, pattern_grade="A")
    rec = r["record"]
    assert rec["type"] == "convergence_record"
    assert set(rec["evidence"]) == {"llm", "zone", "structure", "pattern", "trend", "news"}
    assert rec["confidence"]["p_win"] == r["p_win"]
    assert rec["result"] is None  # filled on close (Verify/Converge)
    assert len(r["why"]) >= 1
