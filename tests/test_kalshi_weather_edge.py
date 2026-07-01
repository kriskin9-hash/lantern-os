"""Tests for the Σ₀ weather-edge probe (experiments/kalshi_weather_edge.py).

These pin the MEASURED conclusions from the 2026-06-30 calibration so they can't
silently drift: the routine day is efficient (no band-robust edge), the extreme
day has the ≥100 °F ceiling active, and the ≥100 fade survives the whole band.
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "experiments"))
import kalshi_weather_edge as kwe  # noqa: E402


def test_routine_day_tail_is_thin():
    # Forecast 96 °F → ≥100 essentially off the table, matching the market's 1¢.
    d = kwe.calibrated_distribution(96, 1, kwe.JUL1_LADDER)
    assert d[">=100"] < 0.03


def test_routine_day_modal_matches_market():
    d = kwe.calibrated_distribution(96, 1, kwe.JUL1_LADDER)
    assert max(d, key=d.get) == "94-95"


def test_routine_day_is_efficient():
    # The point-estimate 'NO 94-95' edge must NOT survive the calibration band —
    # this is the naive-model trap the probe exists to avoid.
    rep = kwe.robust_edge_report(96, 1, kwe.JUL1_LADDER, kwe.JUL1_ASK)
    assert rep["actionable"] == []
    assert rep["verdict"] == "no certified edge"


def test_extreme_day_ceiling_caps_the_tail():
    # Forecast 102 °F: the ≥100 record ceiling keeps P(≥100) far below the naive
    # Gaussian ~0.5 — measured band is (0.05, 0.20).
    d = kwe.calibrated_distribution(102, 3, kwe.HOT_LADDER)
    p100 = d["100-101"] + d[">=102"]
    assert 0.05 < p100 < 0.20


def test_extreme_day_fade_is_band_robust():
    # ≥100 priced richly (40¢) on a 102 °F forecast → NO side clears the whole band.
    rep = kwe.robust_edge_report(102, 3, kwe.HOT_LADDER, kwe.HOTDAY_ASK_HYPO)
    fade = next((r for r in rep["actionable"] if r["bucket"] == "100-101"), None)
    assert fade is not None and fade["side"] == "no" and fade["worst_c"] > 15


def test_distribution_normalizes():
    d = kwe.calibrated_distribution(96, 1, kwe.JUL1_LADDER)
    assert abs(sum(d.values()) - 1.0) < 1e-9


def test_kalshi_fee_formula():
    assert kwe.kalshi_fee_cents(0.40) == 2
    assert kwe.kalshi_fee_cents(0.09) == 1
    assert kwe.kalshi_fee_cents(0.50) == 2


def test_selfcheck_passes():
    assert kwe.selfcheck() == 0


def test_convergence_record_is_grounded_and_modest():
    d = kwe.calibrated_distribution(96, 1, kwe.JUL1_LADDER)
    rep = kwe.robust_edge_report(96, 1, kwe.JUL1_LADDER, kwe.JUL1_ASK)
    rec = kwe.convergence_record("26JUL01", 96, d, rep, ["nws-forecast", "kalshi-live"])
    assert rec["confidence"] <= 0.6          # no confidence laundering
    assert rec["evidence_ids"]               # external grounding present
    assert "KNYC" in rec["grounding"]
