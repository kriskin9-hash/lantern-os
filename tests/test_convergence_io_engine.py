import json
from datetime import datetime, timedelta, timezone

from convergence_io_engine import TesseractEngine, NapSafety, ConvergenceLoop


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


# ══════════════════════════════════════════════════════════════════
#  Digital Blackbox — Internal Acceleration Tests
# ══════════════════════════════════════════════════════════════════


def test_nap_safety_returns_structure_even_without_psutil():
    nap = NapSafety()
    result = nap.check()
    assert "cpu_temp_c" in result
    assert "mem_percent" in result
    assert "throttle" in result
    assert "abort" in result
    assert result["abort"] is False


def _setup_repo_for_loop(tmp_path):
    """Create minimal repo structure so ConvergenceLoop phases pass."""
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    (scripts_dir / "Validate-CicdPipeline.ps1").write_text("# placeholder", encoding="utf-8")
    (tmp_path / "README.md").write_text("# Test\nCurrent Focus: test", encoding="utf-8")
    manifests_dir = tmp_path / "manifests" / "evidence"
    manifests_dir.mkdir(parents=True, exist_ok=True)
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / "CONVERGENCE-LOOP.md").write_text("# doc", encoding="utf-8")
    (docs_dir / "CSF-FORMAT-SPECIFICATION.md").write_text("# spec", encoding="utf-8")


def test_convergence_loop_default_multiplier_is_five(tmp_path):
    _setup_repo_for_loop(tmp_path)
    loop = ConvergenceLoop(repo_root=tmp_path)
    result = loop.run()
    assert result["internal_ticks"] == 5
    assert result["promotion_ready"] is True
    assert result.get("status") != "aborted"
    # External I/O phases only run on the final tick, so total phases =
    # 4 internal ticks * 11 non-external phases + 1 final tick * 13 phases = 57
    assert len(result["phases"]) == 57


def test_convergence_loop_custom_multiplier_and_dilation(tmp_path):
    _setup_repo_for_loop(tmp_path)
    loop = ConvergenceLoop(repo_root=tmp_path, internal_multiplier=2, external_dilation=0.5)
    result = loop.run()
    assert result["internal_ticks"] == 2
    assert result["promotion_ready"] is True
    # 1 internal tick * 11 + 1 final tick * 13 = 24
    assert len(result["phases"]) == 24


def test_convergence_loop_external_io_phases_only_on_final_tick(tmp_path):
    _setup_repo_for_loop(tmp_path)
    loop = ConvergenceLoop(repo_root=tmp_path, internal_multiplier=3)
    result = loop.run()
    names = [p["name"] for p in result["phases"]]
    # record_evidence and promote_or_hold should appear exactly once each
    assert names.count("record_evidence") == 1
    assert names.count("promote_or_hold") == 1
    # Other phases appear on every tick
    assert names.count("inspect_repo") == 3


def test_convergence_loop_respects_zero_multiplier(tmp_path):
    _setup_repo_for_loop(tmp_path)
    loop = ConvergenceLoop(repo_root=tmp_path, internal_multiplier=0)
    result = loop.run()
    # min(1, 0) clamps to 1
    assert result["internal_ticks"] == 1
    assert len(result["phases"]) == 13


def test_convergence_loop_includes_safety_telemetry(tmp_path):
    _setup_repo_for_loop(tmp_path)
    loop = ConvergenceLoop(repo_root=tmp_path, internal_multiplier=1)
    result = loop.run()
    assert "safety" in result
    assert "cpu_temp_c" in result["safety"]
    assert "mem_percent" in result["safety"]
