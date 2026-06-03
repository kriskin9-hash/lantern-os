"""Quantum Dust v0.7 — default free-state for the 3^12 normalized light matrix.

Most of the matrix exists as uncollapsed potential. Only coherent deviations
(observations, anchors, characters) are stored explicitly. This makes
"no change" confirmations nearly free.

v0.7 optimizations:
  1. Delta deduplication: multiple observations on same dim_index are merged.
  2. Cached get_state: LRU cache for repeated position lookups.
  3. Built-in converge() method for one-shot field stabilization.
  4. Active delta compaction: periodic collapse of redundant deltas.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .qutrit_delta import (
    NUM_DIMENSIONS,
    QutritDelta,
    QutritState,
    apply_deltas,
)


# ------------------------------------------------------------------
# Cached state resolution for repeated lookups
# ------------------------------------------------------------------

def _make_key(scalar_pos: int, base_tuple: Tuple[QutritState, ...], delta_tuple: Tuple[QutritDelta, ...]) -> int:
    """Hashable key for state cache."""
    return hash((scalar_pos, base_tuple, delta_tuple))


@dataclass
class QuantumDustField:
    """Represents the 3^12 matrix where most positions are implicit dust.

    The global baseline is the converged, stable state. Positions not in
    the baseline are quantum dust — free to be what they want to be.

    Active deltas track deviations from the baseline. When a delta is
    small enough, convergence collapses it back into the baseline.
    """

    # Global baseline: converged state for specific positions
    # Maps scalar_position -> list of 12 QutritState values
    baseline: Dict[int, List[QutritState]] = field(default_factory=dict)

    # Active deltas: positions currently deviating from baseline
    # Maps scalar_position -> list of QutritDelta
    active_deltas: Dict[int, List[QutritDelta]] = field(default_factory=dict)

    # Dust threshold: positions with total deviation below this are dust
    convergence_threshold: float = 0.08

    # v0.7: private cache for resolved states
    _state_cache: Dict[int, List[QutritState]] = field(default_factory=dict, repr=False)
    _cache_hits: int = field(default=0, repr=False)
    _cache_misses: int = field(default=0, repr=False)

    @property
    def total_positions(self) -> int:
        return 3 ** NUM_DIMENSIONS

    @property
    def baseline_positions(self) -> int:
        return len(self.baseline)

    @property
    def active_positions(self) -> int:
        return len(self.active_deltas)

    @property
    def dust_positions(self) -> int:
        """Positions that are neither in baseline nor have active deltas."""
        return self.total_positions - self.baseline_positions - self.active_positions

    @property
    def dust_percentage(self) -> float:
        return 100.0 * self.dust_positions / self.total_positions

    def get_state(self, scalar_pos: int) -> Optional[List[QutritState]]:
        """Resolve the effective state at a position.

        Priority:
          1. If active deltas exist, apply them to the baseline (or default).
          2. If baseline exists, return it.
          3. Otherwise, return None (quantum dust).

        v0.7: uses an internal cache for repeated lookups of the same
        (position, baseline, deltas) combination.
        """
        base = self.baseline.get(scalar_pos)
        deltas = self.active_deltas.get(scalar_pos)

        if base is not None and deltas is not None:
            # v0.7: cache key based on immutable tuples
            cache_key = _make_key(scalar_pos, tuple(base), tuple(deltas))
            if cache_key in self._state_cache:
                self._cache_hits += 1
                return list(self._state_cache[cache_key])
            self._cache_misses += 1
            result = apply_deltas(base, deltas)
            self._state_cache[cache_key] = result
            return list(result)
        if base is not None:
            return list(base)
        if deltas is not None:
            # No baseline: start from zero-amplitude default
            default = [QutritState(0, 0) for _ in range(NUM_DIMENSIONS)]
            return apply_deltas(default, deltas)
        return None  # Quantum dust

    def observe(self, scalar_pos: int, deltas: List[QutritDelta]) -> None:
        """Record a sensor observation at a position.

        v0.7: deduplicates deltas on the same dim_index, keeping the
        latest value. This prevents unbounded growth when the same
        dimension is observed repeatedly.
        """
        if scalar_pos in self.active_deltas:
            existing = self.active_deltas[scalar_pos]
            # Merge new deltas with existing, keeping latest per dim_index
            merged = {d.dim_index: d for d in existing}
            for d in deltas:
                merged[d.dim_index] = d
            self.active_deltas[scalar_pos] = list(merged.values())
        else:
            self.active_deltas[scalar_pos] = list(deltas)
        # v0.7: invalidate cache for this position
        self._state_cache.clear()

    def confirm(self, scalar_pos: int) -> None:
        """Confirm a position is still at its baseline (cheap heartbeat)."""
        # A confirmation means no active delta needed — remove if present.
        if self.active_deltas.pop(scalar_pos, None):
            self._state_cache.clear()

    def observe_batch(
        self,
        observations: Dict[int, List[QutritDelta]],
        confirmations: Optional[List[int]] = None,
    ) -> None:
        """Batch observation + confirmation for sensor streams."""
        mutated = False
        for pos, deltas in observations.items():
            if pos in self.active_deltas:
                existing = self.active_deltas[pos]
                merged = {d.dim_index: d for d in existing}
                for d in deltas:
                    merged[d.dim_index] = d
                self.active_deltas[pos] = list(merged.values())
            else:
                self.active_deltas[pos] = list(deltas)
            mutated = True
        if confirmations:
            for pos in confirmations:
                if self.active_deltas.pop(pos, None):
                    mutated = True
        if mutated:
            self._state_cache.clear()

    def converge(self, levels: Optional[List[float]] = None) -> List:
        """v0.7: One-shot convergence using the built-in engine.

        Returns a list of ConvergenceResult summaries.
        """
        from .convergence_engine import multi_level_convergence
        results = multi_level_convergence(self, levels=levels)
        # Convergence may have changed states; invalidate cache
        self._state_cache.clear()
        return results

    def compact(self) -> int:
        """v0.7: Compact active deltas by removing zero-magnitude entries.

        Returns the number of deltas removed.
        """
        removed = 0
        for pos in list(self.active_deltas.keys()):
            deltas = self.active_deltas[pos]
            # Keep only non-zero deltas
            compacted = [d for d in deltas if d.amp_delta != 0 or d.phase_delta != 0]
            removed += len(deltas) - len(compacted)
            if compacted:
                self.active_deltas[pos] = compacted
            else:
                del self.active_deltas[pos]
        if removed:
            self._state_cache.clear()
        return removed

    def stats(self) -> Dict[str, float]:
        """Return storage and coverage statistics."""
        total_active_deltas = sum(len(d) for d in self.active_deltas.values())
        cache_hit_rate = (
            self._cache_hits / (self._cache_hits + self._cache_misses)
            if (self._cache_hits + self._cache_misses) > 0
            else 0.0
        )
        return {
            "total_positions": float(self.total_positions),
            "baseline_positions": float(self.baseline_positions),
            "active_positions": float(self.active_positions),
            "dust_positions": float(self.dust_positions),
            "dust_percentage": self.dust_percentage,
            "total_active_deltas": float(total_active_deltas),
            "avg_deltas_per_active": (
                total_active_deltas / self.active_positions
                if self.active_positions else 0.0
            ),
            "cache_hit_rate": cache_hit_rate,
            "cache_size": float(len(self._state_cache)),
        }
