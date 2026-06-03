"""Quantum Dust Field v0.7 — Symbolic-optimized default state.

Identical to v0.6 quantum_dust but with more aggressive defaults
for symbolic data: lower convergence threshold, faster clustering.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .qutrit_delta import NUM_DIMENSIONS, QutritDelta, QutritState, apply_deltas


@dataclass
class QuantumDustField:
    """Symbolic-optimized Quantum Dust field."""

    baseline: Dict[int, List[QutritState]] = field(default_factory=dict)
    active_deltas: Dict[int, List[QutritDelta]] = field(default_factory=dict)
    convergence_threshold: float = 0.06  # More aggressive than v0.6's 0.08

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
        return self.total_positions - self.baseline_positions - self.active_positions

    @property
    def dust_percentage(self) -> float:
        return 100.0 * self.dust_positions / self.total_positions

    def get_state(self, scalar_pos: int) -> Optional[List[QutritState]]:
        base = self.baseline.get(scalar_pos)
        deltas = self.active_deltas.get(scalar_pos)

        if base is not None and deltas is not None:
            return apply_deltas(base, deltas)
        if base is not None:
            return list(base)
        if deltas is not None:
            default = [QutritState(0, 0) for _ in range(NUM_DIMENSIONS)]
            return apply_deltas(default, deltas)
        return None

    def observe(self, scalar_pos: int, deltas: List[QutritDelta]) -> None:
        if scalar_pos in self.active_deltas:
            self.active_deltas[scalar_pos].extend(deltas)
        else:
            self.active_deltas[scalar_pos] = list(deltas)

    def confirm(self, scalar_pos: int) -> None:
        self.active_deltas.pop(scalar_pos, None)

    def stats(self) -> Dict[str, float]:
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
