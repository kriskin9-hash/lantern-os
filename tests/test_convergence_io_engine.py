import json
from datetime import datetime, timedelta, timezone

from convergence_io_engine import TesseractEngine


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _build_engine(tmp_path):
    engine = TesseractEngine(data_dir=str(tmp_path))
    engine.health.check = lambda url: {
        "url": url,
        "ok": True,
        "status": 200,
        "latency_ms": 1.0,
    }
    return engine


def test_health_check_requires_active_worker_or_fresh_listener(tmp_path):
    engine = _build_engine(tmp_path)
    try:
        result = engine.health_check("http://example.test/api/status")
        assert result["http_ok"] is True
        assert result["ok"] is False
        assert result["agent_activity"]["state"] == "idle"
        assert result["agent_activity"]["listener"]["status"] == "missing"
        assert "no active slots" in result["issues"][0]
    finally:
        engine._executor.shutdown(wait=False)


def test_health_check_rejects_stale_listener_manifest(tmp_path):
    now = datetime.now(timezone.utc)
    _write_json(
        tmp_path / "dollhouse" / "agent-checkin-manifest.json",
        {
            "generated_at": now.isoformat(),
            "listener": {
                "agent": "agent_inspector",
                "status": "active",
                "interval_seconds": 60,
                "heartbeat_at": (now - timedelta(minutes=5)).isoformat(),
            },
            "slots": [
                {
                    "slot_id": "checkin-old",
                    "interval_minutes": 30,
                    "agent_type": "dollhouse_monitor",
                    "last_run": (now - timedelta(hours=3)).isoformat(),
                    "status": "active",
                }
            ],
        },
    )

    engine = _build_engine(tmp_path)
    try:
        result = engine.health_check("http://example.test/api/status")
        listener = result["agent_activity"]["listener"]
        assert result["ok"] is False
        assert result["agent_activity"]["state"] == "idle"
        assert listener["source"] == "agent-checkin-manifest"
        assert listener["status"] == "stale"
        assert listener["ready"] is False
    finally:
        engine._executor.shutdown(wait=False)


def test_health_check_accepts_fresh_listener_manifest(tmp_path):
    now = datetime.now(timezone.utc)
    _write_json(
        tmp_path / "dollhouse" / "agent-checkin-manifest.json",
        {
            "generated_at": now.isoformat(),
            "listener": {
                "agent": "agent_inspector",
                "status": "active",
                "interval_seconds": 60,
                "heartbeat_at": (now - timedelta(seconds=20)).isoformat(),
            },
            "slots": [
                {
                    "slot_id": "checkin-fresh",
                    "interval_minutes": 30,
                    "agent_type": "dollhouse_monitor",
                    "last_run": (now - timedelta(minutes=10)).isoformat(),
                    "status": "active",
                }
            ],
        },
    )

    engine = _build_engine(tmp_path)
    try:
        result = engine.health_check("http://example.test/api/status")
        listener = result["agent_activity"]["listener"]
        assert result["ok"] is True
        assert result["agent_activity"]["state"] == "listener"
        assert listener["source"] == "agent-checkin-manifest"
        assert listener["ready"] is True
        assert listener["status"] == "fresh"
    finally:
        engine._executor.shutdown(wait=False)


def test_health_check_counts_any_active_slot_as_operational(tmp_path):
    _write_json(
        tmp_path / "agent-fleet" / "slots.json",
        {
            "version": 1,
            "slots": {
                "dream_journal-verify-req-0001": {
                    "claimed_at": datetime.now(timezone.utc).isoformat(),
                    "status": "active",
                }
            },
        },
    )

    engine = _build_engine(tmp_path)
    try:
        result = engine.health_check("http://example.test/api/status")
        activity = result["agent_activity"]
        inspect = engine.inspect()
        assert result["ok"] is True
        assert activity["state"] == "active"
        assert activity["active_slots"] == 1
        assert activity["dream_journal_slots_active"] == 1
        assert inspect["slots_active"] == 1
        assert inspect["dream_journal_slots_active"] == 1
    finally:
        engine._executor.shutdown(wait=False)


def test_health_check_accepts_fresh_tesseract_listener_snapshot(tmp_path):
    now = datetime.now(timezone.utc)
    _write_json(
        tmp_path / "agent-fleet" / "tesseract-latest.json",
        {
            "timestamp": now.isoformat(),
            "listener": {
                "agent": "agent_inspector",
                "status": "active",
                "interval_seconds": 60,
                "heartbeat_at": (now - timedelta(seconds=10)).isoformat(),
            },
            "dollhouse": {
                "status": "ok",
                "checkin_slots": 6,
            },
        },
    )

    engine = _build_engine(tmp_path)
    try:
        result = engine.health_check("http://example.test/api/status")
        listener = result["agent_activity"]["listener"]
        assert result["ok"] is True
        assert result["agent_activity"]["state"] == "listener"
        assert listener["source"] == "tesseract-latest"
        assert listener["ready"] is True
    finally:
        engine._executor.shutdown(wait=False)
