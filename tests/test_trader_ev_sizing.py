"""
Tests for the Σ₀ trader EV/sizing improvements (convergence_ev):

  1. edge_risk_multiplier — bounded half-Kelly on the flat-$ risk.
  2. target_r consistency — a higher reward:risk raises EV monotonically, so the
     fix that feeds the *real* 3R (vs the old ~2R profile ratio) can only make a
     genuinely-3R setup more likely to clear the EV bar, never a junk one (P_MIN
     and the evidence floor still gate).

Pure module — no Alpaca / OpenAI / DB, so this runs in CI without keys.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "trading_agents"))

from convergence_ev import edge_risk_multiplier, score_convergence, EV_MIN, P_MIN


# ── edge_risk_multiplier ───────────────────────────────────────────────────────

def test_multiplier_is_bounded():
    for p in (0.30, 0.46, 0.5, 0.55, 0.6, 0.7, 0.8, 0.9):
        for r in (1.0, 2.0, 3.0):
            assert 0.5 <= edge_risk_multiplier(p, r) <= 1.5


def test_multiplier_is_risk_neutral_at_coinflip():
    # The whole point of the recalibration: a neutral 50% setup sizes at exactly
    # the flat risk (1.0×), so the scaler does not blanket-inflate risk.
    assert edge_risk_multiplier(0.50, 3.0) == pytest.approx(1.0, abs=1e-6)


def test_multiplier_scales_with_conviction():
    low = edge_risk_multiplier(0.48, 3.0)
    mid = edge_risk_multiplier(0.55, 3.0)
    high = edge_risk_multiplier(0.62, 3.0)
    assert low < mid < high
    assert edge_risk_multiplier(0.60, 3.0) == 1.5    # +0.10 conviction → cap
    assert edge_risk_multiplier(0.40, 3.0) == 0.5    # −0.10 conviction → floor


def test_multiplier_leans_out_on_weak_conviction():
    assert edge_risk_multiplier(0.45, 3.0) == pytest.approx(0.75, abs=1e-6)
    assert edge_risk_multiplier(0.30, 1.5) == 0.5    # far below neutral → floor


def test_multiplier_safe_on_bad_input():
    assert edge_risk_multiplier(None, 3.0) == 1.0
    assert edge_risk_multiplier("x", 3.0) == 1.0
    assert edge_risk_multiplier(0.6, 0) == 1.0       # invalid target_r guard
    assert edge_risk_multiplier(1.5, 3.0) == 1.0     # p out of (0,1)
    assert edge_risk_multiplier(0.6) == 1.5          # target_r optional


# ── target_r consistency in the EV gate ────────────────────────────────────────

def _base_candidate(target_r):
    # A modestly-graded real setup: at a zone, structure shifted, trend aligned.
    return {
        "direction": "BULLISH",
        "in_zone": True, "zone_strength": 60, "zone_touches": 2,
        "structure_shifted": True, "structure_conf": 65,
        "trend_aligned": True,
        "backtest_winrate": 0.5,
        "target_r": target_r,
    }


def test_higher_target_r_raises_ev_monotonically():
    ev2 = score_convergence(_base_candidate(2.0))
    ev3 = score_convergence(_base_candidate(3.0))
    assert ev3["ev_r"] > ev2["ev_r"]          # same p_win, bigger payoff → bigger EV
    assert ev3["p_win"] == ev2["p_win"]        # target_r must not move p_win


def test_evidence_floor_still_gates_regardless_of_target_r():
    # No grounding evidence at all → SKIP even with a huge target_r (can't be
    # carried by an optimistic reward:risk). This is the External-Reality guard.
    naked = {"direction": "BULLISH", "backtest_winrate": 0.8, "target_r": 10.0}
    out = score_convergence(naked)
    assert out["decision"] == "SKIP"


def test_enter_requires_both_ev_and_pwin_bars():
    out = score_convergence(_base_candidate(3.0))
    if out["decision"] == "ENTER":
        assert out["ev_r"] >= EV_MIN and out["p_win"] >= P_MIN
