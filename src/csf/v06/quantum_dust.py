"""Quantum Dust — default free-state for the 3^12 normalized light matrix.

Most of the matrix exists as uncollapsed potential. Only coherent deviations
(observations, anchors, characters) are stored explicitly. This makes
"no change" confirmations nearly free.
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
        """
        base = self.baseline.get(scalar_pos)
        deltas = self.active_deltas.get(scalar_pos)

        if base is not None and deltas is not None:
            return apply_deltas(base, deltas)
        if base is not None:
            return list(base)
        if deltas is not None:
            # No baseline: start from zero-amplitude default
            default = [QutritState(0, 0) for _ in range(NUM_DIMENSIONS)]
            return apply_deltas(default, deltas)
        return None  # Quantum dust

    def observe(self, scalar_pos: int, deltas: List[QutritDelta]) -> None:
        """Record a sensor observation at a position."""
        if scalar_pos in self.active_deltas:
            self.active_deltas[scalar_pos].extend(deltas)
        else:
            self.active_deltas[scalar_pos] = list(deltas)

    def confirm(self, scalar_pos: int) -> None:
        """Confirm a position is still at its baseline (cheap heartbeat)."""
        # A confirmation means no active delta needed — remove if present.
        self.active_deltas.pop(scalar_pos, None)

    def observe_batch(
        self,
        observations: Dict[int, List[QutritDelta]],
        confirmations: Optional[List[int]] = None,
    ) -> None:
        """Batch observation + confirmation for sensor streams."""
        for pos, deltas in observations.items():
            self.observe(pos, deltas)
        if confirmations:
            for pos in confirmations:
                self.confirm(pos)

    def stats(self) -> Dict[str, float]:
        """Return storage and coverage statistics."""
        total_active_deltas = sum(len(d) for d in self.active_deltas.values())
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
        }
