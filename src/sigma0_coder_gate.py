"""Structural Σ₀ gate for local coder output.

This module does not call a model and does not prove code correctness. It checks
whether a local coding-agent response has the minimum evidence shape required by
Lantern Verify before it can be promoted into a convergence record.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable, Mapping, Optional

REQUIRED_SECTIONS: tuple[str, ...] = (
    "claim",
    "evidence",
    "confidence",
    "source",
    "verification",
)


def normalize_evidence(evidence: Optional[Iterable[Mapping[str, Any] | str]]) -> list[dict[str, Any]]:
    """Normalize supplied evidence into claim/source/confidence records."""

    records: list[dict[str, Any]] = []
    if not evidence:
        return records
    for item in evidence:
        if isinstance(item, str):
            claim = item.strip()
            source = "user-supplied"
            confidence = 0.7
        else:
            claim = str(item.get("claim", item.get("text", ""))).strip()
            source = str(item.get("source", "unknown"))
            confidence = float(item.get("confidence", 1.0))
        if claim:
            records.append(
                {
                    "claim": claim,
                    "source": source,
                    "confidence": max(0.0, min(confidence, 1.0)),
                }
            )
    return records


def build_pre_generation_gate(evidence: Optional[Iterable[Mapping[str, Any] | str]] = None) -> dict[str, Any]:
    """Return the confidence cap and required fields before model generation."""

    records = normalize_evidence(evidence)
    grounded = bool(records)
    return {
        "grounded": grounded,
        "max_confidence": 1.0 if grounded else 0.3,
        "required_sections": list(REQUIRED_SECTIONS),
        "evidence": records,
        "missing_evidence": [] if grounded else ["file reads", "test output", "issue text", "operator facts"],
    }


def assess_coder_output(text: str) -> dict[str, Any]:
    """Assess whether output has the required Σ₀ evidence structure."""

    lowered = text.lower()
    present = {section: bool(re.search(rf"(^|\n)\s*{section}\s*:", lowered)) for section in REQUIRED_SECTIONS}
    missing = [section for section, ok in present.items() if not ok]

    confidence_values: list[int] = []
    for match in re.finditer(r"confidence\s*:\s*(\d{1,3})\s*%?", lowered):
        value = int(match.group(1))
        if 0 <= value <= 100:
            confidence_values.append(value)

    return {
        "passed": not missing and bool(confidence_values),
        "missing_sections": missing,
        "confidence_values": confidence_values,
        "max_confidence": max(confidence_values) if confidence_values else None,
    }
