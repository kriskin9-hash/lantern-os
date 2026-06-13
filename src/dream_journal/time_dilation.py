"""Time Dilation Engine — bidirectional internal/external ratio control. ORION v1.0."""

from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .human_observer_hub import ObserverState


@dataclass
class DilationState:
    internal: float
    external: float

    @property
    def ratio(self) -> float:
        if self.external == 0.0:
            return self.internal
        return self.internal / self.external


class TimeDilationEngine:
    """Controls subjective vs objective time ratios.

    internal_multiplier: how many symbolic cycles fit in one external tick.
    external_dilation:   compression of external time (< 1 = slowdown).
    """

    def __init__(self) -> None:
        self.internal: float = 8.0
        self.external: float = 1.0

    def set_from_observer(self, hub_state: "ObserverState") -> float:
        self.internal = float(hub_state.recommended_dilation)
        self.external = max(0.4, 1.0 - (hub_state.focus * 0.6))
        return self.get_ratio()

    def set(self, internal: float, external: float) -> float:
        self.internal = internal
        self.external = max(0.0001, external)
        return self.get_ratio()

    def get_ratio(self) -> float:
        return DilationState(self.internal, self.external).ratio

    def get_state(self) -> DilationState:
        return DilationState(self.internal, self.external)
