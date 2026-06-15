"""Verify stage — fold verification outcomes back into ConvergenceRecords (wq-007).

A ConvergenceRecord starts unverified with a prior confidence. Verification updates
that record from what actually happened — a test/benchmark result, or a Kalman
surprise (NIS) reading from the SurpriseMonitor. This closes Reason → Act → Verify:
claims are graded by evidence, not left at their prior.

- A passing test boosts confidence toward 1.0; a failing test collapses it.
- A high NIS (a "spook" — observation contradicts the model) collapses confidence;
  a consistent NIS nudges it up.

Links to src/cio_sde/surprise.py via its `SurpriseMonitor.evaluate()` output shape
(reads "nis"/"dof"); does not modify that module.
"""
from __future__ import annotations

import math
from typing import Dict, Optional

from .objects import ConvergenceRecord


def verify_with_test(record: ConvergenceRecord, passed: bool,
                     notes: Optional[str] = None) -> ConvergenceRecord:
    """Fold a test/benchmark outcome into the record (mutates + returns it)."""
    if passed:
        record.confidence = min(1.0, 0.5 + 0.5 * record.confidence)
    else:
        record.confidence = max(0.0, record.confidence * 0.2)
    record.verified = True
    record.verification_notes = notes or ("test passed" if passed else "test failed")
    return record


def verify_with_surprise(record: ConvergenceRecord, nis: float, dof: int,
                         spook_sigmas: float = 3.0) -> ConvergenceRecord:
    """Fold a Kalman NIS reading into the record.

    NIS ≫ dof (a spook) means observation contradicts the model → collapse
    confidence. NIS ≈ dof means the claim held → nudge confidence up.
    """
    threshold = dof + spook_sigmas * math.sqrt(2.0 * dof)
    if nis > threshold:
        record.confidence = max(0.0, record.confidence * 0.3)
        record.verification_notes = (
            f"NIS={nis:.1f} > {threshold:.1f} (spook): observation contradicts claim")
    else:
        record.confidence = min(1.0, record.confidence + 0.1 * (1.0 - record.confidence))
        record.verification_notes = f"NIS={nis:.1f} <= {threshold:.1f}: observation consistent"
    record.verified = True
    return record


def verify_with_monitor(record: ConvergenceRecord, monitor_result: Dict,
                        spook_sigmas: float = 3.0) -> ConvergenceRecord:
    """Convenience: fold a SurpriseMonitor.evaluate() result dict into the record.

    Accepts the dict produced by src/cio_sde/surprise.py::SurpriseMonitor.evaluate
    (keys "nis", "dof"); values may be torch tensors or plain floats.
    """
    nis = monitor_result["nis"]
    dof = monitor_result["dof"]
    nis = float(nis.item()) if hasattr(nis, "item") else float(nis)
    dof = int(dof.item()) if hasattr(dof, "item") else int(dof)
    return verify_with_surprise(record, nis, dof, spook_sigmas=spook_sigmas)
