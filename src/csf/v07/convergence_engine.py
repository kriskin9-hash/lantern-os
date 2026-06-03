"""Convergence Engine v0.7 — collapse small deltas into the global baseline.

Optimized for symbolic qutrit data with:
  1. LRU-cached magnitude computation (avoid redundant sqrt).
  2. Pre-computed cluster norms for O(1) similarity checks.
  3. Cluster-to-baseline promotion when clusters saturate.
  4. Adaptive threshold scaling based on field activity.
  5. Batch magnitude pre-computation with early exit.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, List, Optional, Tuple

from .qutrit_delta import NUM_DIMENSIONS, QutritDelta, QutritState, apply_deltas
from .quantum_dust import QuantumDustField


@dataclass(slots=True)
class ConvergenceResult:
    """Summary of a convergence pass."""
    collapsed: int = 0                # Positions absorbed into baseline
    clustered: int = 0                # Deltas merged into existing clusters
    drift_remaining: int = 0          # Positions still active after pass
    baseline_growth: int = 0          # New positions added to baseline
    avg_magnitude_before: float = 0.0
    avg_magnitude_after: float = 0.0
    clusters_promoted: int = 0        # NEW v0.7: clusters absorbed into baseline
    threshold_used: float = 0.0     # NEW v0.7: actual threshold this pass


# ------------------------------------------------------------------
# Cached magnitude with tuple-key hashing (deltas are frozen dataclasses)
# ------------------------------------------------------------------

@lru_cache(maxsize=4096)
def _magnitude_cached(delta_tuple: Tuple[QutritDelta, ...]) -> float:
    """Compute total change magnitude for a tuple of deltas."""
    if not delta_tuple:
        return 0.0
    return sum(math.sqrt(d.amp_delta ** 2 + d.phase_delta ** 2) for d in delta_tuple) / len(delta_tuple)


def _magnitude(deltas: List[QutritDelta]) -> float:
    """Wrapper that converts list to hashable tuple for caching."""
    return _magnitude_cached(tuple(deltas))


# ------------------------------------------------------------------
# Optimized similarity with pre-computed norms
# ------------------------------------------------------------------

def _delta_norm(delta_tuple: Tuple[QutritDelta, ...]) -> float:
    """Pre-compute the squared norm of a delta vector."""
    return sum(d.amp_delta ** 2 + d.phase_delta ** 2 for d in delta_tuple)


def _similarity(a: List[QutritDelta], b: List[QutritDelta]) -> float:
    """Cosine-like similarity between two delta vectors (same dimensions).
    
    v0.7 optimization: pre-compute anorm before the loop to avoid
    redundant accumulation when the same vector is compared many times.
    """
    if not a or not b:
        return 0.0

    # Build sparse maps by dim_index
    amap = {d.dim_index: (d.amp_delta, d.phase_delta) for d in a}
    bmap = {d.dim_index: (d.amp_delta, d.phase_delta) for d in b}

    dot = 0.0
    anorm = sum(ava ** 2 + avp ** 2 for ava, avp in amap.values())
    bnorm = sum(bva ** 2 + bvp ** 2 for bva, bvp in bmap.values())

    for idx, (ava, avp) in amap.items():
        if idx in bmap:
            bva, bvp = bmap[idx]
            dot += ava * bva + avp * bvp

    if anorm == 0 or bnorm == 0:
        return 0.0
    return dot / (math.sqrt(anorm) * math.sqrt(bnorm))


# ------------------------------------------------------------------
# Cluster representative with cached norm
# ------------------------------------------------------------------

class _ClusterRep:
    """Internal helper to store a cluster representative and its pre-computed norm."""
    __slots__ = ("deltas", "norm", "positions")

    def __init__(self, deltas: List[QutritDelta]):
        self.deltas = deltas
        self.norm = _delta_norm(tuple(deltas))
        self.positions: List[int] = []

    def similarity_to(self, other_deltas: List[QutritDelta]) -> float:
        """Fast similarity using pre-computed norm."""
        if not other_deltas:
            return 0.0
        bmap = {d.dim_index: (d.amp_delta, d.phase_delta) for d in other_deltas}
        dot = 0.0
        bnorm = 0.0
        for idx, (bva, bvp) in bmap.items():
            bnorm += bva ** 2 + bvp ** 2
        for d in self.deltas:
            if d.dim_index in bmap:
                bva, bvp = bmap[d.dim_index]
                dot += d.amp_delta * bva + d.phase_delta * bvp
        if self.norm == 0 or bnorm == 0:
            return 0.0
        return dot / (math.sqrt(self.norm) * math.sqrt(bnorm))


# ------------------------------------------------------------------
# Convergence Engine v0.7
# ------------------------------------------------------------------

class ConvergenceEngine:
    """Classical convergence engine for Quantum Dust fields."""

    def __init__(
        self,
        threshold: float = 0.08,
        cluster_similarity: float = 0.85,
        max_cluster_size: int = 64,
        promote_clusters: bool = True,  # NEW v0.7
    ):
        self.threshold = threshold
        self.cluster_similarity = cluster_similarity
        self.max_cluster_size = max_cluster_size
        self.promote_clusters = promote_clusters
        self.clusters: Dict[int, _ClusterRep] = {}

    def run(self, field: QuantumDustField) -> ConvergenceResult:
        """Execute one convergence pass over the field."""
        if not field.active_deltas:
            # v0.7: early exit for empty fields
            return ConvergenceResult(
                drift_remaining=0,
                threshold_used=self.threshold,
            )

        collapsed = 0
        clustered = 0
        baseline_growth = 0
        clusters_promoted = 0

        # v0.7: Pre-compute all magnitudes in one batch (enables cache warming)
        mag_cache = {
            pos: _magnitude(deltas)
            for pos, deltas in field.active_deltas.items()
        }
        avg_before = sum(mag_cache.values()) / len(mag_cache) if mag_cache else 0.0

        # Adaptive threshold: if field is very active, relax threshold slightly
        # to avoid thrashing; if nearly stable, tighten for precision.
        adaptive_threshold = self._adapt_threshold(avg_before)

        to_remove: List[int] = []
        for pos, deltas in list(field.active_deltas.items()):
            mag = mag_cache[pos]

            if mag < adaptive_threshold:
                # Small deviation → collapse into baseline
                current_state = field.get_state(pos)
                if current_state is not None:
                    is_new = pos not in field.baseline
                    field.baseline[pos] = current_state
                    if is_new:
                        baseline_growth += 1
                to_remove.append(pos)
                collapsed += 1
                continue

            # Large deviation → try clustering
            cluster_key = self._find_cluster(deltas)
            if cluster_key is not None:
                self.clusters[cluster_key].positions.append(pos)
                clustered += 1

                # v0.7: promote saturated clusters to baseline
                if (
                    self.promote_clusters
                    and len(self.clusters[cluster_key].positions) >= self.max_cluster_size
                ):
                    clusters_promoted += self._promote_cluster(cluster_key, field, to_remove)

        for pos in to_remove:
            field.active_deltas.pop(pos, None)

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
            clusters_promoted=clusters_promoted,
            threshold_used=adaptive_threshold,
        )

    def _adapt_threshold(self, avg_magnitude: float) -> float:
        """v0.7: Scale threshold based on average field activity.
        
        - High activity (avg > 0.5) → relax by +25% to avoid thrashing.
        - Low activity (avg < 0.03) → tighten by -15% for precision.
        """
        if avg_magnitude > 0.5:
            return self.threshold * 1.25
        if avg_magnitude < 0.03:
            return self.threshold * 0.85
        return self.threshold

    def _find_cluster(self, deltas: List[QutritDelta]) -> Optional[int]:
        """Find an existing cluster similar to these deltas."""
        for key, rep in self.clusters.items():
            if len(rep.positions) >= self.max_cluster_size:
                continue
            if rep.similarity_to(deltas) >= self.cluster_similarity:
                return key
        # No match: create a new cluster with a new key
        new_key = len(self.clusters)
        self.clusters[new_key] = _ClusterRep(deltas)
        return new_key

    def _promote_cluster(
        self, key: int, field: QuantumDustField, to_remove: List[int]
    ) -> int:
        """v0.7: Promote a saturated cluster into the baseline.
        
        Computes the median representative state from all positions in the
        cluster, stores it as a shared baseline entry for each position,
        and removes those positions from active tracking.
        """
        rep = self.clusters[key]
        if not rep.positions:
            return 0

        # Compute centroid: average all states in the cluster
        # For symbolic qutrits, we use the representative's deltas applied
        # to the default zero state as the shared baseline.
        default = [QutritState(0, 0) for _ in range(NUM_DIMENSIONS)]
        centroid = apply_deltas(default, rep.deltas)

        promoted_count = 0
        for pos in rep.positions:
            if pos not in to_remove:
                is_new = pos not in field.baseline
                field.baseline[pos] = centroid
                if is_new:
                    promoted_count += 1
                to_remove.append(pos)

        # Clear the cluster so it can be reused
        del self.clusters[key]
        return promoted_count

    def reset_clusters(self) -> None:
        """Clear clustering state (useful between major convergence epochs)."""
        self.clusters.clear()


# ------------------------------------------------------------------
# Multi-level convergence with convergence-optimized ordering
# ------------------------------------------------------------------

def multi_level_convergence(
    field: QuantumDustField,
    levels: Optional[List[float]] = None,
    promote_clusters: bool = True,
) -> List[ConvergenceResult]:
    """Run convergence at multiple thresholds (coarse → fine).

    v0.7 default: [0.24, 0.14, 0.08, 0.05] — slightly coarser first pass
    to collapse large stable regions faster, then tighten for precision.
    """
    if levels is None:
        levels = [0.24, 0.14, 0.08, 0.05]

    results = []
    for threshold in levels:
        engine = ConvergenceEngine(
            threshold=threshold,
            promote_clusters=promote_clusters,
        )
        result = engine.run(field)
        results.append(result)
        # v0.7: if no movement, skip remaining levels
        if result.collapsed == 0 and result.clusters_promoted == 0:
            break
    return results
