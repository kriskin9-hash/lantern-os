"""Human Observer Hub — real-time human focus engine. ORION v1.0."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ObserverState:
    focus: float = 0.82
    intent: str = ""
    emotion: float = 0.0
    recommended_dilation: int = 20


class HumanObserverHub:
    """Tracks the human observer's focus, intent, and emotional state.

    Feeds directly into TimeDilationEngine to modulate internal/external
    time ratios for the claims packet.
    """

    def __init__(self) -> None:
        self.focus: float = 0.82
        self.symbolic_intent: str = ""
        self.emotion: float = 0.0

    def update(
        self,
        intent: str,
        focus: Optional[float] = None,
        emotion: float = 0.0,
    ) -> ObserverState:
        if focus is not None:
            self.focus = max(0.0, min(1.0, focus))
        self.symbolic_intent = intent
        self.emotion = emotion
        return self.get_state()

    def get_state(self) -> ObserverState:
        return ObserverState(
            focus=self.focus,
            intent=self.symbolic_intent,
            emotion=self.emotion,
            recommended_dilation=6 + int(self.focus * 18),
        )
