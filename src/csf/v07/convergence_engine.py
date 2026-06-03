"""Convergence Engine v0.7 — Symbolic-optimized, aggressive collapse.

Runs continuous background passes with these symbolic-aware heuristics:

  • Lower magnitude threshold (0.06 vs 0.08) — symbolic data has
    smaller but meaningful deltas that should converge quickly.
  • Cluster similarity bumped to 0.90 — symbolic deltas often
    share structure (same anchors, same emotional patterns).
  • Promote recurring patterns directly into baseline without
    waiting for full stability — trust the symbolic dictionary.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from .qutrit_delta import NUM_DIMENSIONS, QutritDelta, QutritState, apply_deltas
from .quantum_dust import QuantumDustField


@dataclass
class ConvergenceResult:
    collapsed: int
    clustered: int
    drift_remaining: int
    baseline_growth: int
    avg_magnitude_before: float
    avg_magnitude_after: float


def _magnitude(deltas: List[QutritDelta]) -> float:
    if not deltas:
        return 0.0
    return sum(math.sqrt(d.amp_delta ** 2 + d.phase_delta ** 2) for d in deltas) / len(deltas)


def _similarity(a: List[QutritDelta], b: List[QutritDelta]) -> float:
    if not a or not b:
        return 0.0
    amap = {d.dim_index: (d.amp_delta, d.phase_delta) for d in a}
    bmap = {d.dim_index: (d.amp_delta, d.phase_delta) for d in b}
    dot = 0.0
    anorm = 0.0
    bnorm = 0.0
    for idx, (ava, avp) in amap.items():
        anorm += ava ** 2 + avp ** 2
        if idx in bmap:
            bva, bvp = bmap[idx]
            dot += ava * bva + avp * bvp
    for bva, bvp in bmap.values():
        bnorm += bva ** 2 + bvp ** 2
    if anorm == 0 or bnorm == 0:
        return 0.0
    return dot / (math.sqrt(anorm) * math.sqrt(bnorm))


class ConvergenceEngine:
    """Symbolic-optimized convergence."""

    def __init__(
        self,
        threshold: float = 0.06,
        cluster_similarity: float = 0.90,
        max_cluster_size: int = 128,
    ):
        self.threshold = threshold
        self.cluster_similarity = cluster_similarity
        self.max_cluster_size = max_cluster_size
        self.clusters: Dict[int, List[Tuple[int, List[QutritDelta]]]] = {}

    def run(self, field: QuantumDustField) -> ConvergenceResult:
        collapsed = 0
        clustered = 0
        baseline_growth = 0

        all_mags = [_magnitude(d) for d in field.active_deltas.values()]
        avg_before = sum(all_mags) / len(all_mags) if all_mags else 0.0

        to_remove: List[int] = []
        for pos, deltas in list(field.active_deltas.items()):
            mag = _magnitude(deltas)

            if mag < self.threshold:
                current = field.get_state(pos)
                if current is not None:
                    field.baseline[pos] = current
                    baseline_growth += 1 if pos not in field.baseline else 0
                to_remove.append(pos)
                collapsed += 1
                continue

            cluster_key = self._find_cluster(deltas)
            if cluster_key is not None:
                self.clusters.setdefault(cluster_key, []).append((pos, deltas))
                clustered += 1

        for pos in to_remove:
            del field.active_deltas[pos]

        all_mags_after = [_magnitude(d) for d in field.active_deltas.values()]
        avg_after = sum(all_mags_after) / len(all_mags_after) if all_mags_after else 0.0

        return ConvergenceResult(
            collapsed=collapsed,
            clustered=clustered,
            drift_remaining=len(field.active_deltas),
            baseline_growth=baseline_growth,
            avg_magnitude_before=avg_before,
            avg_magnitude_after=avg_after,
        )

    def _find_cluster(self, deltas: List[QutritDelta]) -> Optional[int]:
        for key, members in self.clusters.items():
            if len(members) >= self.max_cluster_size:
                continue
            rep = members[0][1]
            if _similarity(deltas, rep) >= self.cluster_similarity:
                return key
        new_key = len(self.clusters)
        self.clusters[new_key] = []
        return new_key

    def reset_clusters(self) -> None:
        self.clusters.clear()


def multi_level_convergence(
    field: QuantumDustField,
    levels: List[float] = None,
) -> List[ConvergenceResult]:
    if levels is None:
        levels = [0.25, 0.15, 0.10, 0.06, 0.04]
    results = []
    for threshold in levels:
        engine = ConvergenceEngine(threshold=threshold)
        result = engine.run(field)
        results.append(result)
    return results
