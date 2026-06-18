"""wq-014 — Kernel.initialize() boots all core objects + a startup health check."""
from src.convergence.kernel import Kernel


def test_initialize_returns_true(tmp_path):
    k = Kernel(memory_path=str(tmp_path / "mem.jsonl"))
    assert k.initialize() is True


def test_health_check_reports_core_and_optional_components(tmp_path):
    k = Kernel(memory_path=str(tmp_path / "mem.jsonl"))
    k.initialize()
    h = k.health_check()
    assert h["ok"] is True
    # core objects
    assert h["components"]["memory"] is True
    assert h["components"]["tools_registry"] is True
    assert h["components"]["convergence_records"] is True
    # optional wired modules (present after wq-006 / wq-007)
    assert h["components"]["router"] is True
    assert h["components"]["verify"] is True


def test_initialize_populates_health_and_components(tmp_path):
    k = Kernel(memory_path=str(tmp_path / "mem.jsonl"))
    k.initialize()
    assert k.health.get("ok") is True
    assert k.components.get("memory") is True


def test_core_objects_wired(tmp_path):
    k = Kernel(memory_path=str(tmp_path / "mem.jsonl"))
    k.initialize()
    assert isinstance(k.tools, dict)
    assert isinstance(k.convergence_records, list)
    assert isinstance(k.memory, dict)


def test_health_counts_present(tmp_path):
    k = Kernel(memory_path=str(tmp_path / "mem.jsonl"))
    k.initialize()
    h = k.health_check()
    for key in ("memory_count", "tools_count", "records_count", "completed_tasks"):
        assert key in h and isinstance(h[key], int)
