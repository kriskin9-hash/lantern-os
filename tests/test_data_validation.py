"""
Data Validation Tests

Validates data files, JSON schemas, and data integrity
for Lantern OS data structures.
"""
import pytest
import json
from pathlib import Path


def test_arc_reactor_status_exists():
    """Verify Arc Reactor status file exists."""
    status_file = Path("data/arc-reactor/status.json")
    assert status_file.exists()


def test_arc_reactor_status_is_valid_json():
    """Verify Arc Reactor status is valid JSON."""
    status_file = Path("data/arc-reactor/status.json")
    content = status_file.read_text(encoding="utf-8")
    
    data = json.loads(content)
    assert isinstance(data, dict)


def test_arc_reactor_status_has_required_fields():
    """Verify Arc Reactor status has required fields."""
    status_file = Path("data/arc-reactor/status.json")
    content = status_file.read_text(encoding="utf-8")
    
    data = json.loads(content)
    
    required_fields = [
        "modelVersion",
        "generatedAt",
    ]
    
    for field in required_fields:
        assert field in data, f"Arc Reactor status missing field: {field}"


def test_kalshi_data_directory_exists():
    """Verify Kalshi data directory exists."""
    kalshi_dir = Path("data/kalshi")
    assert kalshi_dir.exists()


def test_kalshi_kill_switch_exists():
    """Verify Kalshi kill switch file exists."""
    kill_switch = Path("data/kalshi/LIVE-KILL-SWITCH")
    assert kill_switch.exists()


def test_kalshi_kill_switch_has_content():
    """Verify Kalshi kill switch has explanatory content."""
    kill_switch = Path("data/kalshi/LIVE-KILL-SWITCH")
    content = kill_switch.read_text(encoding="utf-8")
    
    assert len(content) > 50, "Kill switch should have explanatory content"
    assert "DISARMED" in content or "ARMED" in content


def test_kalshi_paper_ledger_exists():
    """Verify Kalshi paper ledger exists."""
    ledger = Path("data/kalshi/kalshi-paper-ledger.jsonl")
    assert ledger.exists()


def test_kalshi_paper_ledger_is_valid_jsonl():
    """Verify Kalshi paper ledger is valid JSONL."""
    ledger = Path("data/kalshi/kalshi-paper-ledger.jsonl")
    content = ledger.read_text(encoding="utf-8")
    
    lines = content.strip().split("\n")
    for line in lines:
        if line.strip():
            data = json.loads(line)
            assert isinstance(data, dict)


def test_kalshi_watchlist_exists():
    """Verify Kalshi watchlist exists."""
    watchlist = Path("data/kalshi/kalshi-watchlist-latest.json")
    assert watchlist.exists()


def test_kalshi_watchlist_is_valid_json():
    """Verify Kalshi watchlist is valid JSON."""
    watchlist = Path("data/kalshi/kalshi-watchlist-latest.json")
    content = watchlist.read_text(encoding="utf-8")
    
    data = json.loads(content)
    assert isinstance(data, dict)


def test_baseline_model_exists():
    """Verify baseline model exists."""
    baseline = Path("data/baseline-model/v1.json")
    assert baseline.exists()


def test_baseline_model_is_valid_json():
    """Verify baseline model is valid JSON."""
    baseline = Path("data/baseline-model/v1.json")
    content = baseline.read_text(encoding="utf-8")
    
    data = json.loads(content)
    assert isinstance(data, dict)


def test_validation_directory_has_json_files():
    """Verify validation directory has JSON files."""
    validation_dir = Path("manifests/validation")
    json_files = list(validation_dir.glob("*.json"))
    
    assert len(json_files) > 0, "Validation directory should have JSON files"


def test_validation_json_files_are_valid():
    """Verify validation JSON files are valid."""
    validation_dir = Path("manifests/validation")
    json_files = list(validation_dir.glob("*.json"))
    
    for json_file in json_files:
        content = json_file.read_text(encoding="utf-8")
        data = json.loads(content)
        assert isinstance(data, dict)


def test_evidence_directory_has_files():
    """Verify evidence directory has files."""
    evidence_dir = Path("manifests/evidence")
    files = list(evidence_dir.glob("*.md"))
    
    assert len(files) > 0, "Evidence directory should have markdown files"


def test_data_directory_structure():
    """Verify data directory has proper structure."""
    data_dir = Path("data")
    
    required_subdirs = [
        "kalshi",
        "arc-reactor",
        "baseline-model",
    ]
    
    for subdir in required_subdirs:
        assert (data_dir / subdir).exists(), f"Missing data subdirectory: {subdir}"


def test_json_files_have_no_syntax_errors():
    """Verify all JSON files in repo are valid."""
    json_files = list(Path(".").rglob("*.json"))
    
    # Filter out node_modules
    json_files = [f for f in json_files if "node_modules" not in str(f) and ".git" not in str(f)]
    
    for json_file in json_files:
        try:
            content = json_file.read_text(encoding="utf-8")
            json.loads(content)
        except json.JSONDecodeError as e:
            pytest.fail(f"Invalid JSON in {json_file}: {e}")


def test_jsonl_files_are_valid():
    """Verify all JSONL files in repo are valid."""
    jsonl_files = list(Path(".").rglob("*.jsonl"))
    
    # Filter out node_modules
    jsonl_files = [f for f in jsonl_files if "node_modules" not in str(f) and ".git" not in str(f)]
    
    for jsonl_file in jsonl_files:
        content = jsonl_file.read_text(encoding="utf-8")
        lines = content.strip().split("\n")
        for line in lines:
            if line.strip():
                try:
                    json.loads(line)
                except json.JSONDecodeError as e:
                    pytest.fail(f"Invalid JSONL in {jsonl_file}: {e}")


def test_data_files_are_not_empty():
    """Verify data files are not empty."""
    data_dir = Path("data")
    
    for data_file in data_dir.rglob("*"):
        if data_file.is_file() and not data_file.name.startswith("."):
            if data_file.suffix in [".json", ".jsonl", ".md"]:
                content = data_file.read_text(encoding="utf-8")
                assert len(content.strip()) > 0, f"Data file is empty: {data_file}"
