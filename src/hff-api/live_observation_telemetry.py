#!/usr/bin/env python3
"""
Live observation telemetry contract.

This module defines the exact public status semantics needed to tell whether
live sensors are merely registered, actually running, producing measurements,
updating beliefs, producing corrections, or failing.

The data exposed here is intentionally best-effort. It proves local runtime
activity, not independent truth. Do not label live sensor data verified unless a
separate provenance/freshness verification layer exists.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


DATA_MODE_BEST_EFFORT = "best_effort"
STATUS_NOT_ENABLED = "not_enabled"
STATUS_REGISTERED_NOT_RUN = "registered_not_run"
STATUS_RUNNING = "running"
STATUS_RAN_NO_MEASUREMENTS = "ran_no_measurements"
STATUS_RAN_WITH_UPDATES = "ran_with_updates"
STATUS_RAN_WITH_MEASUREMENTS_NO_UPDATES = "ran_with_measurements_no_updates"
STATUS_FAILED = "failed"


@dataclass
class LiveObservationTelemetry:
    """Runtime telemetry for one live observation loop.

    The fields are designed to remove ambiguity from `corrections_count=0`.
    Zero corrections can be healthy if measurements updated beliefs but did not
    cross the correction threshold. It is suspicious if sensors never ran, failed,
    or produced measurements that updated nothing.
    """

    enabled: bool = False
    data_mode: str = DATA_MODE_BEST_EFFORT
    sensor_count: int = 0
    observation_count: int = 0
    last_observation_started_at: Optional[str] = None
    last_observation_finished_at: Optional[str] = None
    last_measurement_count: int = 0
    last_update_count: int = 0
    last_correction_count: int = 0
    last_error_count: int = 0
    last_errors: List[str] = field(default_factory=list)

    def mark_enabled(self, sensor_count: int) -> None:
        """Mark live observation as enabled and record registered sensors."""
        self.enabled = True
        self.sensor_count = max(0, int(sensor_count))

    def start_observation(self) -> None:
        """Record the start of a live observation cycle."""
        self.last_observation_started_at = _now_iso()
        self.last_observation_finished_at = None
        self.last_measurement_count = 0
        self.last_update_count = 0
        self.last_correction_count = 0
        self.last_error_count = 0
        self.last_errors = []

    def finish_observation(
        self,
        measurement_count: int,
        update_count: int,
        correction_count: int,
        errors: Optional[List[str]] = None,
    ) -> None:
        """Record the end of a live observation cycle."""
        self.observation_count += 1
        self.last_observation_finished_at = _now_iso()
        self.last_measurement_count = max(0, int(measurement_count))
        self.last_update_count = max(0, int(update_count))
        self.last_correction_count = max(0, int(correction_count))
        self.last_errors = list(errors or [])
        self.last_error_count = len(self.last_errors)

    def record_failure(self, error: Exception | str) -> None:
        """Record a failed observation cycle without hiding the reason."""
        self.observation_count += 1
        self.last_observation_finished_at = _now_iso()
        self.last_measurement_count = 0
        self.last_update_count = 0
        self.last_correction_count = 0
        self.last_errors = [str(error)]
        self.last_error_count = 1

    def status_reason(self) -> str:
        """Return the exact state represented by the current telemetry."""
        if not self.enabled:
            return STATUS_NOT_ENABLED
        if (
            self.last_observation_started_at is not None
            and self.last_observation_finished_at is None
        ):
            return STATUS_RUNNING
        if self.observation_count == 0:
            return STATUS_REGISTERED_NOT_RUN
        if self.last_error_count > 0:
            return STATUS_FAILED
        if self.last_measurement_count == 0:
            return STATUS_RAN_NO_MEASUREMENTS
        if self.last_update_count == 0:
            return STATUS_RAN_WITH_MEASUREMENTS_NO_UPDATES
        return STATUS_RAN_WITH_UPDATES

    def to_dict(self) -> Dict[str, Any]:
        """JSON-safe public status payload."""
        return {
            "enabled": self.enabled,
            "data_mode": self.data_mode,
            "best_effort": self.data_mode == DATA_MODE_BEST_EFFORT,
            "sensor_count": self.sensor_count,
            "observation_count": self.observation_count,
            "last_observation_started_at": self.last_observation_started_at,
            "last_observation_finished_at": self.last_observation_finished_at,
            "last_measurement_count": self.last_measurement_count,
            "last_update_count": self.last_update_count,
            "last_correction_count": self.last_correction_count,
            "last_error_count": self.last_error_count,
            "last_errors": self.last_errors,
            "status_reason": self.status_reason(),
        }


def summarize_belief_activity(beliefs: Dict[str, Any], live_updated_entities=None) -> Dict[str, int]:
    """Summarize seeded-only vs live-updated belief activity.

    Parameters
    ----------
    beliefs:
        Mapping of entity key to belief-like objects.
    live_updated_entities:
        Iterable of entity keys updated by live observations in this process.

    Returns a JSON-safe count summary. This deliberately avoids claiming
    verification; live-updated means only that this runtime saw a live update.
    """
    live_updated = set(live_updated_entities or [])
    belief_keys = set(beliefs.keys())
    live_updated_belief_count = len(belief_keys & live_updated)
    belief_count = len(belief_keys)
    seeded_only_belief_count = max(0, belief_count - live_updated_belief_count)
    return {
        "belief_count": belief_count,
        "seeded_only_belief_count": seeded_only_belief_count,
        "live_updated_belief_count": live_updated_belief_count,
    }


def classify_belief_data_mode(entity: str, live_updated_entities=None) -> Dict[str, Any]:
    """Classify a belief for public display.

    Current implementation has only two honest modes:
    - seeded_baseline: no live update recorded for this entity in this runtime
    - live_best_effort: live update recorded, but not independently verified
    """
    live_updated = set(live_updated_entities or [])
    if entity in live_updated:
        return {
            "data_mode": "live_best_effort",
            "best_effort": True,
            "last_source_type": "live",
        }
    return {
        "data_mode": "seeded_baseline",
        "best_effort": True,
        "last_source_type": "seeded",
    }


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
