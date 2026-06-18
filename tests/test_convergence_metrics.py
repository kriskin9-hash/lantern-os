"""wq-013 — convergence metrics tracking over time."""
from src.convergence.objects import ConvergenceRecord
from src.convergence.metrics import snapshot_metrics, ConvergenceTracker


def _recs(confidences, verified=True):
    return [
        ConvergenceRecord(id=f"r{i}", hypothesis="h", evidence_ids=[], result=None,
                          confidence=c, reasoner="t", verified=verified)
        for i, c in enumerate(confidences)
    ]


def test_snapshot_counts_and_rates():
    s = snapshot_metrics(_recs([0.9, 0.8, 0.3]))
    assert s["verified_records"] == 3
    assert s["success_rate"] == 2 / 3  # 0.9, 0.8 > 0.7
    assert s["failure_rate"] == 1 / 3  # 0.3 < 0.5
    assert abs(s["mean_confidence"] - (0.9 + 0.8 + 0.3) / 3) < 1e-9


def test_snapshot_ignores_unverified_for_rates():
    s = snapshot_metrics(_recs([0.9, 0.9], verified=False))
    assert s["verified_records"] == 0
    assert s["mean_confidence"] == 0.0
    assert s["total_records"] == 2


def test_tracker_accumulates_history():
    t = ConvergenceTracker()
    t.record(_recs([0.5]))
    t.record(_recs([0.9]))
    assert len(t.history) == 2


def test_confidence_growth_positive_when_improving():
    t = ConvergenceTracker()
    t.record(_recs([0.4, 0.5]))
    t.record(_recs([0.8, 0.9]))
    assert t.confidence_growth() > 0


def test_failure_reduction_and_converging():
    t = ConvergenceTracker()
    t.record(_recs([0.3, 0.3, 0.9]))   # high failure rate
    t.record(_recs([0.9, 0.9, 0.9]))   # no failures
    assert t.failure_reduction() > 0
    assert t.is_converging() is True


def test_not_converging_when_confidence_falls():
    t = ConvergenceTracker()
    t.record(_recs([0.9, 0.9]))
    t.record(_recs([0.3, 0.3]))
    assert t.is_converging() is False


def test_single_snapshot_not_converging():
    t = ConvergenceTracker()
    t.record(_recs([0.9]))
    assert t.is_converging() is False
    assert t.trajectory()["snapshots"] == 1
