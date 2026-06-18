"""wq-011 — pattern extraction over high-confidence verified ConvergenceRecords."""
from src.convergence.objects import ConvergenceRecord
from src.convergence.pattern_extractor import extract_patterns, DEFAULT_MIN_CONFIDENCE


def _rec(conf, reasoner="router", hyp="route to X", verified=True, ev=("m1",)):
    return ConvergenceRecord(
        id=f"r-{conf}-{reasoner}-{hyp}", hypothesis=hyp, evidence_ids=list(ev),
        result=None, confidence=conf, reasoner=reasoner, verified=verified,
    )


def test_filters_below_confidence_threshold():
    recs = [_rec(0.9), _rec(0.5), _rec(0.7)]
    pats = extract_patterns(recs)
    assert len(pats) == 1
    assert pats[0]["mean_confidence"] >= DEFAULT_MIN_CONFIDENCE


def test_requires_verified_by_default():
    recs = [_rec(0.95, verified=False)]
    assert extract_patterns(recs) == []
    assert len(extract_patterns(recs, require_verified=False)) == 1


def test_groups_by_reasoner_and_hypothesis():
    recs = [_rec(0.9, "router", "A"), _rec(0.95, "router", "A"), _rec(0.9, "dream", "A")]
    pats = extract_patterns(recs)
    assert len(pats) == 2  # (router,A) and (dream,A)
    router_a = next(p for p in pats if p["reasoner"] == "router")
    assert router_a["support"] == 2


def test_mean_confidence_and_evidence_count():
    recs = [_rec(0.9, ev=("m1", "m2")), _rec(1.0, ev=("m3",))]
    pats = extract_patterns(recs)
    assert pats[0]["support"] == 2
    assert abs(pats[0]["mean_confidence"] - 0.95) < 1e-9
    assert pats[0]["evidence_count"] == 3


def test_sorted_strongest_first():
    recs = [_rec(0.86, "a", "lo"), _rec(0.99, "b", "hi")]
    pats = extract_patterns(recs)
    assert pats[0]["hypothesis"] == "hi"


def test_empty_input():
    assert extract_patterns([]) == []
