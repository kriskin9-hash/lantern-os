#!/usr/bin/env python3
"""Backward-compatible iPhone Shortcut telemetry adapter.

The generic implementation now lives in device_telemetry.py. This module keeps
phone-specific names for existing callers/tests while routing through the shared
DeviceTelemetrySensor and sanitizer.
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping

from device_telemetry import (
    ALLOWED_BATTERY_STATES,
    ALLOWED_MANUAL_MODES,
    BLOCKED_DEVICE_TELEMETRY_FRAGMENTS,
    DeviceTelemetrySensor,
    blocked_device_telemetry_fields,
    sanitize_device_payload,
)


ALLOWED_PHONE_TELEMETRY_FIELDS = frozenset({
    "device_id",
    "battery_level",
    "battery_state",
    "manual_mode",
    "shortcut_version",
    "operator_note",
    "recorded_at",
})

BLOCKED_PHONE_TELEMETRY_FRAGMENTS = BLOCKED_DEVICE_TELEMETRY_FRAGMENTS


def blocked_phone_telemetry_fields(payload: Mapping[str, Any]) -> List[str]:
    """Return payload keys that look like disallowed private phone data."""
    return blocked_device_telemetry_fields(payload)


def sanitize_phone_payload(payload: Mapping[str, Any]) -> Dict[str, Any]:
    """Validate and sanitize a coarse iPhone Shortcut telemetry payload.

    This accepts the original phone-specific `shortcut_version` field and maps
    it to the generic device telemetry `client_version` field.
    """
    if not isinstance(payload, Mapping):
        raise ValueError("phone telemetry payload must be a JSON object")

    translated: Dict[str, Any] = dict(payload)
    if "shortcut_version" in translated and "client_version" not in translated:
        translated["client_version"] = translated.pop("shortcut_version")

    translated.setdefault("device_kind", "phone")
    translated.setdefault("device_label", "Alex iPhone")

    sanitized = sanitize_device_payload(translated)
    return {
        "device_id": sanitized["device_id"],
        "battery_level": sanitized["battery_level"],
        "battery_state": sanitized["battery_state"],
        "manual_mode": sanitized["manual_mode"],
        "shortcut_version": sanitized["client_version"],
        "operator_note": sanitized["operator_note"],
        "client_recorded_at": sanitized["client_recorded_at"],
    }


class PhoneShortcutSensor(DeviceTelemetrySensor):
    """Phone-specific wrapper around the generic device telemetry sensor."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("sensor_id", "alex-iphone-shortcut")
        kwargs.setdefault("scope", "operator:alex:iphone")
        super().__init__(*args, **kwargs)

    def update_payload(self, payload: Mapping[str, Any]) -> Dict[str, Any]:
        """Store a sanitized latest phone payload and return phone-shaped data."""
        phone_sanitized = sanitize_phone_payload(payload)
        device_payload = {
            "device_id": phone_sanitized["device_id"],
            "device_kind": "phone",
            "device_label": "Alex iPhone",
            "battery_level": phone_sanitized["battery_level"],
            "battery_state": phone_sanitized["battery_state"],
            "manual_mode": phone_sanitized["manual_mode"],
            "client_version": phone_sanitized["shortcut_version"],
            "operator_note": phone_sanitized["operator_note"],
            "recorded_at": phone_sanitized["client_recorded_at"],
        }
        self._latest_payload = device_payload
        return phone_sanitized
