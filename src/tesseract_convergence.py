"""
Tesseract Convergence Engine -- Lantern OS (Backward Compatibility Shim)

This module re-exports the Convergence I/O Engine for backward compatibility.
The full implementation lives in convergence_io_engine.py.
"""

from __future__ import annotations

from convergence_io_engine import (
    CircuitBreaker,
    CircuitState,
    ConvergenceContext,
    ConvergenceLoop,
    HealthProbe,
    Layer,
    MetricsCollector,
    PhaseResult,
    PromotionState,
    SlotManager,
    TesseractCell,
    TesseractEngine,
)

__all__ = [
    "CircuitBreaker",
    "CircuitState",
    "ConvergenceContext",
    "ConvergenceLoop",
    "HealthProbe",
    "Layer",
    "MetricsCollector",
    "PhaseResult",
    "PromotionState",
    "SlotManager",
    "TesseractCell",
    "TesseractEngine",
]
