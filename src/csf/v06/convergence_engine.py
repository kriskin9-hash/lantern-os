"""Convergence Engine — collapse small deltas into the global baseline.

Runs as a background pass over the Quantum Dust field:
  1. Measure total deviation magnitude at each active position.
  2. If below threshold → absorb into baseline (promote stable state).
  3. If above threshold → cluster similar deltas or keep as drift.
  4. Remove positions that fully converged.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from .qutrit_delta import NUM_DIMENSIONS, QutritDelta, QutritState, apply_deltas
from .quantum_dust import QuantumDustField


@dataclass
class ConvergenceResult:
    """Summary of a convergence pass."""
    collapsed: int                # Positions absorbed into baseline
    clustered: int              # Deltas merged into existing clusters
    drift_remaining: int          # Positions still active after pass
    baseline_growth: int        # New positions added to baseline
    avg_magnitude_before: float
    avg_magnitude_after: float


def _magnitude(deltas: List[QutritDelta]) -> float:
    """Compute total change magnitude for a list of deltas."""
    if not deltas:
        return 0.0
    return sum(math.sqrt(d.amp_delta ** 2 + d.phase_delta ** 2) for d in deltas) / len(deltas)


def _similarity(a: List[QutritDelta], b: List[QutritDelta]) -> float:
    """Cosine-like similarity between two delta vectors (same dimensions)."""
    if not a or not b:
        return 0.0

    # Build sparse maps by dim_index
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
    """Classical convergence engine for Quantum Dust fields."""

    def __init__(
        self,
        threshold: float = 0.08,
        cluster_similarity: float = 0.85,
        max_cluster_size: int = 64,
    ):
        self.threshold = threshold
        self.cluster_similarity = cluster_similarity
        self.max_cluster_size = max_cluster_size
        self.clusters: Dict[int, List[Tuple[int, List[QutritDelta]]]] = {}

    def run(self, field: QuantumDustField) -> ConvergenceResult:
        """Execute one convergence pass over the field."""
        collapsed = 0
        clustered = 0
        baseline_growth = 0

        # Compute magnitudes before
        all_mags = [
            _magnitude(deltas)
            for deltas in field.active_deltas.values()
        ]
        avg_before = sum(all_mags) / len(all_mags) if all_mags else 0.0

        # Process each active position
        to_remove: List[int] = []
        for pos, deltas in list(field.active_deltas.items()):
            mag = _magnitude(deltas)

            if mag < self.threshold:
                # Small deviation → collapse into baseline
                current_state = field.get_state(pos)
                if current_state is not None:
                    field.baseline[pos] = current_state
                    baseline_growth += 1 if pos not in field.baseline else 0
                to_remove.append(pos)
                collapsed += 1
                continue

            # Large deviation → try clustering
            cluster_key = self._find_cluster(deltas)
            if cluster_key is not None:
                self.clusters.setdefault(cluster_key, []).append((pos, deltas))
                clustered += 1
                # After clustering, if cluster is big enough, we could
                # promote a representative to baseline. For now, keep active.

        for pos in to_remove:
            del field.active_deltas[pos]

        # Recompute magnitudes after
        all_mags_after = [
            _magnitude(deltas)
            for deltas in field.active_deltas.values()
        ]
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
        """Find an existing cluster similar to these deltas."""
        for key, members in self.clusters.items():
            if len(members) >= self.max_cluster_size:
                continue
            # Compare against cluster representative (first member)
            rep = members[0][1]
            if _similarity(deltas, rep) >= self.cluster_similarity:
                return key
        # No match: create a new cluster with a new key
        new_key = len(self.clusters)
        self.clusters[new_key] = []
        return new_key

    def reset_clusters(self) -> None:
        """Clear clustering state (useful between major convergence epochs)."""
        self.clusters.clear()


def multi_level_convergence(
    field: QuantumDustField,
    levels: List[float] = None,
) -> List[ConvergenceResult]:
    """Run convergence at multiple thresholds (coarse → fine).

    Default: [0.20, 0.12, 0.08, 0.05]
    """
    if levels is None:
        levels = [0.20, 0.12, 0.08, 0.05]

    results = []
    for threshold in levels:
        engine = ConvergenceEngine(threshold=threshold)
        result = engine.run(field)
        results.append(result)
    return results
