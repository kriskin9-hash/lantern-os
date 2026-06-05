import importlib.util
import json
from pathlib import Path


def _load_agent_inspector():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "agent_inspector.py"
    spec = importlib.util.spec_from_file_location("agent_inspector", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_refresh_checkin_manifest_writes_listener_heartbeat(tmp_path, monkeypatch):
    module = _load_agent_inspector()
    checkin_path = tmp_path / "dollhouse" / "agent-checkin-manifest.json"
    csf_path = tmp_path / "dollhouse" / "csf" / "manifest.json"
    csf_path.parent.mkdir(parents=True, exist_ok=True)
    csf_path.write_text(
        json.dumps(
            {
                "checkin_slots": [
                    {
                        "slot_id": "checkin-001",
                        "segment_id": "seg-001",
                        "interval_minutes": 30,
                        "agent_type": "dollhouse_monitor",
                        "status": "active",
                    }
                ]
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(module, "CHECKIN_MANIFEST_PATH", checkin_path)
    monkeypatch.setattr(module, "CSF_MANIFEST_PATH", csf_path)

    manifest = module.refresh_checkin_manifest(45)
    written = json.loads(checkin_path.read_text(encoding="utf-8"))

    assert manifest["listener"]["agent"] == "agent_inspector"
    assert manifest["listener"]["status"] == "active"
    assert manifest["listener"]["interval_seconds"] == 45
    assert written["listener"]["heartbeat_at"]
    assert len(written["slots"]) == 1


def test_acquire_listener_lock_rejects_duplicate_owner(tmp_path, monkeypatch):
    module = _load_agent_inspector()
    lock_path = tmp_path / "agent-fleet" / "tesseract-listener.lock.json"

    monkeypatch.setattr(module, "LISTENER_LOCK_PATH", lock_path)
    monkeypatch.setattr(module, "_pid_running", lambda pid: True)

    assert module.acquire_listener_lock(60) is True
    assert module.acquire_listener_lock(60) is False
