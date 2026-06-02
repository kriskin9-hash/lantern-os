"""Safe opt-in background mode for HFF.

Background mode is deliberately narrow:

- disabled by default;
- opt-in through HFF_BACKGROUND_MODE=true;
- bounded to an eight-hour operator sleep window by default;
- local in-process heartbeat only;
- no network access;
- no sensors;
- no mesh sync;
- no writes;
- no personal data collection;
- no actuator/device behavior;
- visible through public status.

It gives operators a safe way to verify that a deployment can sustain a bounded
background worker without silently expanding authority. The operator-facing
private shorthand may call this convergence; public status keeps the neutral
background-window language.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import os
import threading
import time
from typing import Any

_TRUE_VALUES = {"1", "true", "yes", "on"}
DEFAULT_BACKGROUND_WINDOW_HOURS = 8.0
MAX_BACKGROUND_WINDOW_HOURS = 8.0
SECONDS_PER_HOUR = 60.0 * 60.0


def env_flag(name: str, default: bool = False) -> bool:
    """Read a boolean env flag using HFF's common truthy values."""
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in _TRUE_VALUES


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def bounded_window_hours(raw: str | None) -> float:
    """Return the requested background window clamped to the safe pilot bound."""
    if raw is None:
        return DEFAULT_BACKGROUND_WINDOW_HOURS
    try:
        requested = float(raw)
    except ValueError:
        return DEFAULT_BACKGROUND_WINDOW_HOURS
    if requested <= 0:
        return DEFAULT_BACKGROUND_WINDOW_HOURS
    return min(requested, MAX_BACKGROUND_WINDOW_HOURS)


@dataclass
class BackgroundModeController:
    """Small in-process background heartbeat controller.

    This is not an agent runner, queue worker, scheduler, telemetry loop, sensor
    poller, or mesh node. It only updates in-memory status so background-mode
    lifecycle can be proven without hidden side effects.
    """

    enabled: bool = False
    interval_seconds: float = 60.0
    window_hours: float = DEFAULT_BACKGROUND_WINDOW_HOURS
    started_at: str | None = None
    last_tick_at: str | None = None
    tick_count: int = 0
    mode: str = "disabled"
    _started_monotonic: float | None = field(default=None, init=False, repr=False)
    _thread: threading.Thread | None = field(default=None, init=False, repr=False)
    _stop: threading.Event = field(default_factory=threading.Event, init=False, repr=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)

    @property
    def window_seconds(self) -> float:
        return max(self.window_hours, 0.0) * SECONDS_PER_HOUR

    def start(self) -> bool:
        """Start background heartbeat if enabled.

        Returns True only when a worker is started or already running. Disabled
        controllers do nothing and return False.
        """
        if not self.enabled:
            with self._lock:
                self.mode = "disabled"
            return False

        with self._lock:
            if self._thread and self._thread.is_alive():
                return True
            self.mode = "heartbeat_only"
            self.started_at = utc_now_iso()
            self.last_tick_at = self.started_at
            self.tick_count = 0
            self._started_monotonic = time.monotonic()
            self._stop.clear()
            self._thread = threading.Thread(
                target=self._run,
                name="hff-background-heartbeat",
                daemon=True,
            )
            self._thread.start()
            return True

    def stop(self) -> None:
        self._stop.set()
        thread = self._thread
        if thread and thread.is_alive():
            thread.join(timeout=min(self.interval_seconds, 1.0))

    def _elapsed_seconds_unlocked(self) -> float:
        if self._started_monotonic is None:
            return 0.0
        return max(time.monotonic() - self._started_monotonic, 0.0)

    def _remaining_seconds_unlocked(self) -> float | None:
        if self._started_monotonic is None:
            return None
        return max(self.window_seconds - self._elapsed_seconds_unlocked(), 0.0)

    def _run(self) -> None:
        while not self._stop.is_set():
            with self._lock:
                remaining = self._remaining_seconds_unlocked()
                if remaining is not None and remaining <= 0:
                    self.mode = "completed"
                    return
                wait_for = min(self.interval_seconds, remaining or self.interval_seconds)
            if self._stop.wait(wait_for):
                return
            self.tick()

    def tick(self) -> None:
        """Record a heartbeat tick without external side effects."""
        with self._lock:
            remaining = self._remaining_seconds_unlocked()
            if remaining is not None and remaining <= 0:
                self.mode = "completed"
                return
            self.tick_count += 1
            self.last_tick_at = utc_now_iso()

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            running = bool(self._thread and self._thread.is_alive())
            elapsed_seconds = self._elapsed_seconds_unlocked() if self.started_at else None
            remaining_seconds = self._remaining_seconds_unlocked()
            if self.enabled and self.started_at and remaining_seconds == 0 and not running:
                self.mode = "completed"
            return {
                "enabled": self.enabled,
                "running": running,
                "mode": self.mode if self.enabled else "disabled",
                "started_at": self.started_at,
                "last_tick_at": self.last_tick_at,
                "tick_count": self.tick_count,
                "window": {
                    "target_hours": self.window_hours,
                    "target_seconds": self.window_seconds,
                    "elapsed_seconds": elapsed_seconds,
                    "remaining_seconds": remaining_seconds,
                    "state": self.mode if self.enabled else "disabled",
                    "max_hours": MAX_BACKGROUND_WINDOW_HOURS,
                    "goal": "8_hour_background_window",
                },
                "side_effects": {
                    "network": False,
                    "live_sensors": False,
                    "mesh_sync": False,
                    "public_writes": False,
                    "personal_data": False,
                    "device_or_actuator_control": False,
                },
                "revocation": "unset HFF_BACKGROUND_MODE or restart with HFF_BACKGROUND_MODE=false",
            }


def create_background_controller_from_env() -> BackgroundModeController:
    interval_raw = os.environ.get("HFF_BACKGROUND_INTERVAL_SECONDS", "60")
    try:
        interval = max(float(interval_raw), 1.0)
    except ValueError:
        interval = 60.0
    return BackgroundModeController(
        enabled=env_flag("HFF_BACKGROUND_MODE", default=False),
        interval_seconds=interval,
        window_hours=bounded_window_hours(os.environ.get("HFF_BACKGROUND_WINDOW_HOURS")),
    )
