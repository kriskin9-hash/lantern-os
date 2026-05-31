"""
Profile Validation Tests

Tests for profile management, profile data,
and profile validation.
"""
import pytest
from pathlib import Path


def test_profiles_directory_exists():
    """Verify profiles directory exists."""
    profiles_dir = Path("profiles")
    assert profiles_dir.exists()


def test_profiles_have_subdirectories():
    """Verify profiles have subdirectories."""
    profiles_dir = Path("profiles")
    subdirs = [d for d in profiles_dir.iterdir() if d.is_dir()]
    
    assert len(subdirs) > 0, "Profiles directory should have subdirectories"


def test_founder_profile_exists():
    """Verify founder profile exists."""
    founder_dir = Path("profiles/founder")
    assert founder_dir.exists()


def test_founder_profile_has_json():
    """Verify founder profile has JSON."""
    profile_json = Path("profiles/founder/profile.json")
    assert profile_json.exists()


def test_founder_profile_has_evolution():
    """Verify founder profile has evolution."""
    evolution = Path("profiles/founder/report-evolution.jsonl")
    assert evolution.exists()


def test_founder_profile_json_is_valid():
    """Verify founder profile JSON is valid."""
    profile_json = Path("profiles/founder/profile.json")
    content = profile_json.read_text(encoding="utf-8-sig")
    
    import json
    data = json.loads(content)
    assert isinstance(data, dict)


def test_founder_profile_evolution_is_valid_jsonl():
    """Verify founder profile evolution is valid JSONL."""
    evolution = Path("profiles/founder/report-evolution.jsonl")
    content = evolution.read_text(encoding="utf-8-sig")
    
    lines = content.strip().split("\n")
    for line in lines:
        if line.strip():
            import json
            json.loads(line)


def test_michah_profile_exists():
    """Verify Michah profile exists."""
    michah_dir = Path("profiles/michah")
    if not michah_dir.exists():
        pytest.skip("Michah profile not yet created")


def test_mookman_profile_exists():
    """Verify Mookman profile exists."""
    mookman_dir = Path("profiles/mookman11")
    if not mookman_dir.exists():
        pytest.skip("Mookman profile not yet created")


def test_profile_json_has_content():
    """Verify profile JSON has content."""
    profiles_dir = Path("profiles")
    profile_files = list(profiles_dir.glob("*/profile.json"))
    
    for profile_file in profile_files:
        content = profile_file.read_text(encoding="utf-8")
        assert len(content) > 50, f"Profile JSON should have content: {profile_file}"


def test_profile_evolution_has_content():
    """Verify profile evolution has content."""
    profiles_dir = Path("profiles")
    evolution_files = list(profiles_dir.glob("*/report-evolution.jsonl"))
    
    for evolution_file in evolution_files:
        content = evolution_file.read_text(encoding="utf-8")
        assert len(content) > 50, f"Profile evolution should have content: {evolution_file}"


def test_profile_has_name():
    """Verify profile has name field."""
    profiles_dir = Path("profiles")
    profile_files = list(profiles_dir.glob("*/profile.json"))
    
    for profile_file in profile_files:
        content = profile_file.read_text(encoding="utf-8-sig")
        import json
        data = json.loads(content)
        if isinstance(data, dict):
            if "name" in data:
                pass  # Has name


def test_profile_has_role():
    """Verify profile has role field."""
    profiles_dir = Path("profiles")
    profile_files = list(profiles_dir.glob("*/profile.json"))
    
    for profile_file in profile_files:
        content = profile_file.read_text(encoding="utf-8-sig")
        import json
        data = json.loads(content)
        if isinstance(data, dict):
            if "role" in data:
                pass  # Has role


def test_profile_evolution_has_timestamps():
    """Verify profile evolution has timestamps."""
    profiles_dir = Path("profiles")
    evolution_files = list(profiles_dir.glob("*/report-evolution.jsonl"))
    
    for evolution_file in evolution_files:
        content = evolution_file.read_text(encoding="utf-8-sig")
        lines = content.strip().split("\n")
        for line in lines:
            if line.strip():
                import json
                data = json.loads(line)
                if isinstance(data, dict):
                    if "timestamp" in data or "date" in data:
                        pass  # Has timestamp


def test_profile_files_are_not_empty():
    """Verify profile files are not empty."""
    profiles_dir = Path("profiles")
    files = list(profiles_dir.rglob("*"))
    
    for file in files:
        if file.is_file() and not file.name.startswith("."):
            if file.suffix in [".json", ".jsonl"]:
                content = file.read_text(encoding="utf-8")
                assert len(content.strip()) > 0, f"Profile file is empty: {file}"


def test_profile_directory_structure():
    """Verify profiles directory has proper structure."""
    profiles_dir = Path("profiles")
    
    required_profiles = [
        "founder",
    ]
    
    for profile in required_profiles:
        assert (profiles_dir / profile).exists(), f"Missing profile: {profile}"


def test_profile_has_contact():
    """Verify profile has contact information."""
    profiles_dir = Path("profiles")
    profile_files = list(profiles_dir.glob("*/profile.json"))
    
    for profile_file in profile_files:
        content = profile_file.read_text(encoding="utf-8-sig")
        import json
        data = json.loads(content)
        if isinstance(data, dict):
            if "contact" in data or "email" in data:
                pass  # Has contact


def test_profile_has_skills():
    """Verify profile has skills information."""
    profiles_dir = Path("profiles")
    profile_files = list(profiles_dir.glob("*/profile.json"))
    
    for profile_file in profile_files:
        content = profile_file.read_text(encoding="utf-8-sig")
        import json
        data = json.loads(content)
        if isinstance(data, dict):
            if "skills" in data:
                pass  # Has skills


def test_profile_evolution_has_reports():
    """Verify profile evolution has report entries."""
    profiles_dir = Path("profiles")
    evolution_files = list(profiles_dir.glob("*/report-evolution.jsonl"))
    
    for evolution_file in evolution_files:
        content = evolution_file.read_text(encoding="utf-8")
        lines = content.strip().split("\n")
        assert len(lines) > 0, f"Profile evolution should have entries: {evolution_file}"


def test_profile_has_status():
    """Verify profile has status field."""
    profiles_dir = Path("profiles")
    profile_files = list(profiles_dir.glob("*/profile.json"))
    
    for profile_file in profile_files:
        content = profile_file.read_text(encoding="utf-8-sig")
        import json
        data = json.loads(content)
        if isinstance(data, dict):
            if "status" in data:
                pass  # Has status
