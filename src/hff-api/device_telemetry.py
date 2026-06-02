#!/usr/bin/env python3
"""Privacy-bounded telemetry sensors for operator-approved devices.

This module generalizes the iPhone Shortcut sensor into a reusable device
telemetry adapter. Phones, watches, laptops, desktops, Raspberry Pis, game
consoles, and other operator-approved devices can all emit bounded HFF
Measurement objects without adding surveillance fields by default.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Mapping, Optional

from sensors import Measurement, Sensor


DEVICE_KINDS = frozenset({
    "phone",
    "watch",
    "tablet",
    "laptop",
    "desktop",
    "raspberry_pi",
    "server",
    "game_console",
    "browser",
    "shortcut",
    "unknown",
})

ALLOWED_DEVICE_TELEMETRY_FIELDS = frozenset({
    "device_id",
    "device_kind",
    "device_label",
    "battery_level",
    "battery_state",
    "power_state",
    "network_state",
    "manual_mode",
    "client_version",
    "operator_note",
    "recorded_at",
    "client_recorded_at",
})

BLOCKED_DEVICE_TELEMETRY_FRAGMENTS = (
    "location",
    "gps",
    "latitude",
    "longitude",
    "coordinate",
    "address",
    "contact",
    "message",
    "call_log",
    "photo",
    "microphone",
    "audio",
    "camera",
    "video",
    "health",
    "biometric",
    "sleep",
    "calendar",
    "browser_history",
    "notification",
    "ssid",
    "bssid",
    "bluetooth",
    "nearby_device",
)

ALLOWED_BATTERY_STATES = frozenset({"charging", "unplugged", "full", "unknown"})
ALLOWED_POWER_STATES = frozenset({"charging", "plugged_in", "battery", "full", "unknown"})
ALLOWED_NETWORK_STATES = frozenset({"online", "offline", "wifi", "cellular", "ethernet", "unknown"})
ALLOWED_MANUAL_MODES = frozenset({"awake", "working", "sleep_soon", "traveling", "idle", "unknown"})

MAX_DEVICE_ID_LENGTH = 80
MAX_DEVICE_LABEL_LENGTH = 80
MAX_VERSION_LENGTH = 80
MAX_OPERATOR_NOTE_LENGTH = 160


def normalise_device_key(key: Any) -> str:
    """Normalize a JSON key for allowlist/blocklist checks."""
    return str(key).strip().lower().replace("-", "_").replace(" ", "_")


def bounded_text(value: Any, default: str, max_length: int) -> str:
    """Return a stripped bounded text value."""
    if value is None:
        return default
    text = str(value).strip()
    if not text:
        return default
    return text[:max_length]


def choice(value: Any, allowed: frozenset[str], default: str) -> str:
    """Normalize a bounded enum-like field."""
    text = bounded_text(value, default, 64).lower().replace(" ", "_").replace("-", "_")
    return text if text in allowed else default


def coerce_battery_level(value: Any) -> Optional[int]:
    """Coerce battery level to an integer percentage in [0, 100]."""
    if value is None or value == "":
        return None

    if isinstance(value, str):
        value = value.strip().rstrip("%")

    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None

    if numeric < 0 or numeric > 100:
        return None
    return int(round(numeric))


def blocked_device_telemetry_fields(payload: Mapping[str, Any]) -> List[str]:
    """Return payload keys that look like disallowed private device data."""
    blocked: List[str] = []
    for key in payload.keys():
        normalised = normalise_device_key(key)
        if any(fragment in normalised for fragment in BLOCKED_DEVICE_TELEMETRY_FRAGMENTS):
            blocked.append(str(key))
    return sorted(blocked)


def sanitize_device_payload(payload: Mapping[str, Any]) -> Dict[str, Any]:
    """Validate and sanitize a coarse operator-approved device telemetry payload."""
    if not isinstance(payload, Mapping):
        raise ValueError("device telemetry payload must be a JSON object")

    blocked = blocked_device_telemetry_fields(payload)
    if blocked:
        raise ValueError("blocked_device_telemetry_fields: " + ", ".join(blocked))

    normalised_keys = {normalise_device_key(key) for key in payload.keys()}
    unsupported = sorted(normalised_keys - ALLOWED_DEVICE_TELEMETRY_FIELDS)
    if unsupported:
        raise ValueError("unsupported_device_telemetry_fields: " + ", ".join(unsupported))

    by_key = {normalise_device_key(key): value for key, value in payload.items()}
    device_kind = choice(by_key.get("device_kind"), DEVICE_KINDS, "unknown")
    battery_state = choice(by_key.get("battery_state"), ALLOWED_BATTERY_STATES, "unknown")
    power_state = choice(by_key.get("power_state"), ALLOWED_POWER_STATES, battery_state)
    recorded_at = by_key.get("recorded_at", by_key.get("client_recorded_at"))

    return {
        "device_id": bounded_text(
            by_key.get("device_id"),
            "unknown_device",
            MAX_DEVICE_ID_LENGTH,
        ),
        "device_kind": device_kind,
        "device_label": bounded_text(
            by_key.get("device_label"),
            "unknown device",
            MAX_DEVICE_LABEL_LENGTH,
        ),
        "battery_level": coerce_battery_level(by_key.get("battery_level")),
        "battery_state": battery_state,
        "power_state": power_state,
        "network_state": choice(
            by_key.get("network_state"),
            ALLOWED_NETWORK_STATES,
            "unknown",
        ),
        "manual_mode": choice(
            by_key.get("manual_mode"),
            ALLOWED_MANUAL_MODES,
            "unknown",
        ),
        "client_version": bounded_text(
            by_key.get("client_version"),
            "unknown",
            MAX_VERSION_LENGTH,
        ),
        "operator_note": bounded_text(
            by_key.get("operator_note"),
            "",
            MAX_OPERATOR_NOTE_LENGTH,
        ),
        "client_recorded_at": bounded_text(
            recorded_at,
            "unknown",
            64,
        ),
    }


class DeviceTelemetrySensor(Sensor):
    """A bounded sensor adapter for coarse telemetry from any approved device.

    The sensor observes only explicitly supplied payloads or an injected payload
    provider. It does not access devices directly and does not collect private
    device data by default.
    """

    def __init__(
        self,
        sensor_id: str = "operator-device-telemetry",
        scope: str = "operator:device",
        payload_provider: Optional[Callable[[], Mapping[str, Any]]] = None,
    ):
        super().__init__(
            sensor_id=sensor_id,
            domain="device_telemetry",
            scope=scope,
        )
        self._payload_provider = payload_provider
        self._latest_payload: Optional[Mapping[str, Any]] = None

    def update_payload(self, payload: Mapping[str, Any]) -> Dict[str, Any]:
        """Store a sanitized latest payload and return the sanitized copy."""
        sanitized = sanitize_device_payload(payload)
        self._latest_payload = sanitized
        return sanitized

    def observe(self) -> List[Measurement]:
        """Return one Measurement for the current device payload, if available."""
        try:
            payload = self._payload_provider() if self._payload_provider else self._latest_payload
            if payload is None:
                self._last_error = "no_device_payload_available"
                return []

            sanitized = sanitize_device_payload(payload)
            now = datetime.now(timezone.utc)
            measurement = Measurement(
                value=sanitized,
                uncertainty=0.35,
                confidence_interval=(0.0, 1.0),
                sample_size=1,
                confounders=[
                    "operator_controlled_device_client",
                    "manual_mode_self_reported",
                    "device_client_may_fail_or_be_stale",
                ],
                missing=[
                    "no_precise_location",
                    "no_health_data",
                    "no_contacts",
                    "no_messages",
                    "no_audio",
                    "no_camera",
                    "no_notification_content",
                    "no_raw_network_identifiers",
                ],
                source=f"device_client:{sanitized['device_kind']}",
                methodology="operator_approved_device_heartbeat",
                temporal_range=("instant", "instant"),
                scope=self.scope,
                recorded_at=now,
            )
            self._last_observation = now
            self._observation_count += 1
            self._last_error = None
            return [measurement]
        except Exception as exc:
            self._error_count += 1
            self._last_error = str(exc)
            return []
