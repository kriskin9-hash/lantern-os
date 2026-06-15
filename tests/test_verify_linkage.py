"""wq-007 — verification outcomes update ConvergenceRecord confidence (Verify stage)."""
from src.convergence.objects import ConvergenceRecord
from src.convergence.verify import (
    verify_with_test, verify_with_surprise, verify_with_monitor,
)


def _rec(conf=0.6):
    return ConvergenceRecord(
        id="cr-1", hypothesis="h", evidence_ids=["m1"], result="r",
        confidence=conf, reasoner="test",
    )


def test_passing_test_boosts_and_marks_verified():
    r = verify_with_test(_rec(0.6), passed=True)
    assert r.verified is True
    assert r.confidence > 0.6
    assert "passed" in r.verification_notes


def test_failing_test_collapses_confidence():
    r = verify_with_test(_rec(0.9), passed=False)
    assert r.verified is True
    assert r.confidence < 0.9
    assert r.confidence <= 0.2 * 0.9 + 1e-9


def test_high_nis_spook_collapses_confidence():
    r = verify_with_surprise(_rec(0.8), nis=500.0, dof=4)
    assert r.verified is True
    assert r.confidence < 0.8
    assert "spook" in r.verification_notes


def test_consistent_nis_nudges_up():
    r = verify_with_surprise(_rec(0.6), nis=4.0, dof=4)
    assert r.confidence > 0.6
    assert "consistent" in r.verification_notes


def test_confidence_stays_in_unit_interval():
    hi = verify_with_test(_rec(1.0), passed=True)
    lo = verify_with_test(_rec(0.0), passed=False)
    assert 0.0 <= hi.confidence <= 1.0
    assert 0.0 <= lo.confidence <= 1.0


def test_verify_with_monitor_reads_dict():
    # mirrors SurpriseMonitor.evaluate() output (plain floats here)
    r = verify_with_monitor(_rec(0.7), {"nis": 999.0, "dof": 6})
    assert r.verified is True
    assert r.confidence < 0.7  # a spook contradicts the claim
