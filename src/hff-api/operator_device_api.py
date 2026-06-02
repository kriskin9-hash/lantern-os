#!/usr/bin/env python3
"""Default-closed operator device telemetry API blueprint.

This module exposes a small Flask blueprint for operator-approved device
heartbeats. It intentionally stores only the latest sanitized heartbeat in
process memory and returns only schema-bounded fields.
"""

from __future__ import annotations

import hmac
import os
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Mapping, Optional

from flask import Blueprint, jsonify, request

from device_telemetry import sanitize_device_payload


DEFAULT_DEVICE_TOKEN_ENV = "HFF_DEVICE_TELEMETRY_TOKEN"
DEVICE_TOKEN_HEADER = "X-HFF-Device-Token"
WRITE_TOKEN_HEADER = "X-HFF-Write-Token"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _request_bearer_or_header(header_name: str) -> str:
    supplied = request.headers.get(header_name, "")
    auth = request.headers.get("Authorization", "")
    if auth.lower().startswith("bearer "):
        supplied = auth[7:].strip()
    return supplied


def _token_matches(supplied: str, expected: str) -> bool:
    return bool(supplied and expected and hmac.compare_digest(supplied, expected))


def _default_token_provider() -> Dict[str, str]:
    return {
        "device": os.environ.get(DEFAULT_DEVICE_TOKEN_ENV, ""),
        "write": os.environ.get("HFF_WRITE_TOKEN", ""),
    }


class LatestDeviceTelemetryStore:
    """Latest-only in-memory store for sanitized device telemetry."""

    def __init__(self):
        self._latest: Optional[Dict[str, Any]] = None

    def set_latest(self, payload: Mapping[str, Any]) -> Dict[str, Any]:
        sanitized = sanitize_device_payload(payload)
        record = {
            "status": "accepted",
            "server_recorded_at": _utc_now(),
            "telemetry": sanitized,
        }
        self._latest = record
        return record

    def get_latest(self) -> Optional[Dict[str, Any]]:
        if self._latest is None:
            return None
        return {
            "status": self._latest["status"],
            "server_recorded_at": self._latest["server_recorded_at"],
            "telemetry": dict(self._latest["telemetry"]),
        }


def _require_device_grant(token_provider: Callable[[], Mapping[str, str]]):
    supplied = _request_bearer_or_header(DEVICE_TOKEN_HEADER)
    tokens = token_provider()

    if _token_matches(supplied, tokens.get("device", "")):
        return None

    write_supplied = request.headers.get(WRITE_TOKEN_HEADER, "")
    if _token_matches(write_supplied, tokens.get("write", "")):
        return None

    return jsonify({
        "error": "device_telemetry_grant_required",
        "message": (
            "Device telemetry writes require HFF_DEVICE_TELEMETRY_TOKEN "
            "or HFF_WRITE_TOKEN operator fallback."
        ),
    }), 403


def _public_latest_payload(record: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    if record is None:
        return {
            "status": "empty",
            "telemetry": None,
        }
    return {
        "status": "ok",
        "server_recorded_at": record["server_recorded_at"],
        "telemetry": record["telemetry"],
    }


def create_device_telemetry_blueprint(
    store: Optional[LatestDeviceTelemetryStore] = None,
    token_provider: Callable[[], Mapping[str, str]] = _default_token_provider,
) -> Blueprint:
    """Create a Flask blueprint for bounded operator device telemetry."""
    telemetry_store = store or LatestDeviceTelemetryStore()
    blueprint = Blueprint("operator_device_telemetry", __name__)

    @blueprint.route("/api/operator/device/heartbeat", methods=["POST"])
    def operator_device_heartbeat():
        grant_error = _require_device_grant(token_provider)
        if grant_error is not None:
            return grant_error

        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return jsonify({"error": "json_object_required"}), 400

        try:
            record = telemetry_store.set_latest(payload)
        except ValueError as exc:
            return jsonify({
                "error": "invalid_device_telemetry",
                "message": str(exc),
            }), 400

        return jsonify(record), 200

    @blueprint.route("/api/operator/device/latest", methods=["GET"])
    def operator_device_latest():
        return jsonify(_public_latest_payload(telemetry_store.get_latest())), 200

    return blueprint


__all__ = [
    "DEFAULT_DEVICE_TOKEN_ENV",
    "DEVICE_TOKEN_HEADER",
    "LatestDeviceTelemetryStore",
    "create_device_telemetry_blueprint",
]
