"""Converge stage — extract reusable patterns from high-confidence records (wq-011).

A periodic batch job: scan ConvergenceRecords, keep the verified high-confidence
ones (the system's reliable reasoning), and summarize them into patterns grouped by
(reasoner, hypothesis). These patterns can be stored back as Memory so future
reasoning is faster and better grounded — the Converge stage of the loop.

Decoupled from the Kernel (operates on any iterable of ConvergenceRecords) so it can
run as a standalone batch job over a records log. Kept as a single module to avoid
sprawl (no separate convergence.py).
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, Iterable, List

from .objects import ConvergenceRecord

DEFAULT_MIN_CONFIDENCE = 0.85


def extract_patterns(records: Iterable[ConvergenceRecord],
                     min_confidence: float = DEFAULT_MIN_CONFIDENCE,
                     require_verified: bool = True) -> List[Dict[str, Any]]:
    """Summarize high-confidence verified records into patterns.

    Groups eligible records by (reasoner, hypothesis); each pattern reports its
    support count, mean confidence, and total grounding evidence. Sorted strongest
    first (mean_confidence, then support).
    """
    eligible = [
        r for r in records
        if r.confidence >= min_confidence and (r.verified or not require_verified)
    ]
    groups: Dict[tuple, List[ConvergenceRecord]] = defaultdict(list)
    for r in eligible:
        groups[(r.reasoner, r.hypothesis)].append(r)

    patterns: List[Dict[str, Any]] = []
    for (reasoner, hypothesis), recs in groups.items():
        patterns.append({
            "hypothesis": hypothesis,
            "reasoner": reasoner,
            "support": len(recs),
            "mean_confidence": sum(r.confidence for r in recs) / len(recs),
            "evidence_count": sum(len(r.evidence_ids) for r in recs),
        })
    patterns.sort(key=lambda p: (p["mean_confidence"], p["support"]), reverse=True)
    return patterns
