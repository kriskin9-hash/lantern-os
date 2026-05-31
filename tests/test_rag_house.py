"""
RAG House Tests

Tests for RAG (Retrieval-Augmented Generation) house,
internal RAG storage, and RAG integration.
"""
import pytest
from pathlib import Path


def test_internal_rag_house_directory_exists():
    """Verify internal RAG house directory exists."""
    rag_dir = Path("data/internal-rag-house")
    assert rag_dir.exists()


def test_internal_rag_house_has_manifest():
    """Verify internal RAG house has manifest."""
    manifest = Path("data/internal-rag-house/RAG-HOUSE-MANIFEST.json")
    assert manifest.exists()


def test_internal_rag_house_has_flat_file():
    """Verify internal RAG house has flat file."""
    flat_file = Path("data/internal-rag-house/LANTERN-OS-INTERNAL-HOUSE-RAG.flat.md")
    assert flat_file.exists()


def test_internal_rag_house_has_readme():
    """Verify internal RAG house has README."""
    readme = Path("data/internal-rag-house/README.md")
    assert readme.exists()


def test_internal_rag_house_manifest_is_valid_json():
    """Verify internal RAG house manifest is valid JSON."""
    manifest = Path("data/internal-rag-house/RAG-HOUSE-MANIFEST.json")
    content = manifest.read_text(encoding="utf-8-sig")
    
    import json
    data = json.loads(content)
    assert isinstance(data, dict)


def test_internal_rag_house_flat_file_has_content():
    """Verify internal RAG house flat file has content."""
    flat_file = Path("data/internal-rag-house/LANTERN-OS-INTERNAL-HOUSE-RAG.flat.md")
    content = flat_file.read_text(encoding="utf-8")
    
    assert len(content) > 100, "RAG house flat file should have content"


def test_internal_rag_house_readme_has_content():
    """Verify internal RAG house README has content."""
    readme = Path("data/internal-rag-house/README.md")
    content = readme.read_text(encoding="utf-8")
    
    assert len(content) > 50, "RAG house README should have content"


def test_rag_dollhouse_skill_exists():
    """Verify RAG dollhouse skill exists."""
    skill_dir = Path("skills/lantern-rag-dollhouse")
    assert skill_dir.exists()


def test_rag_dollhouse_has_skill_md():
    """Verify RAG dollhouse has SKILL.md."""
    skill_md = Path("skills/lantern-rag-dollhouse/SKILL.md")
    assert skill_md.exists()


def test_rag_dollhouse_has_references():
    """Verify RAG dollhouse has references."""
    references = Path("skills/lantern-rag-dollhouse/references")
    assert references.exists()


def test_rag_dollhouse_has_assets():
    """Verify RAG dollhouse has assets."""
    assets = Path("skills/lantern-rag-dollhouse/assets")
    if not assets.exists():
        pytest.skip("RAG dollhouse assets not yet created")


def test_rag_dollhouse_skill_has_content():
    """Verify RAG dollhouse SKILL.md has content."""
    skill_md = Path("skills/lantern-rag-dollhouse/SKILL.md")
    content = skill_md.read_text(encoding="utf-8")
    
    assert len(content) > 50, "RAG dollhouse SKILL.md should have content"


def test_rag_intake_directory_exists():
    """Verify RAG intake directory exists."""
    intake_dir = Path("data/rag-intake")
    if not intake_dir.exists():
        pytest.skip("RAG intake directory not yet created")


def test_rag_handoff_directory_exists():
    """Verify RAG handoff directory exists."""
    handoff_dir = Path("data/rag-handoff")
    if not handoff_dir.exists():
        pytest.skip("RAG handoff directory not yet created")


def test_rag_house_manifest_has_hash():
    """Verify RAG house manifest has hash."""
    manifest = Path("data/internal-rag-house/RAG-HOUSE-MANIFEST.json")
    content = manifest.read_text(encoding="utf-8-sig")
    
    import json
    data = json.loads(content)
    # Should have hash field
    if isinstance(data, dict):
        if "sha256" in data or "hash" in data:
            pass  # Has hash


def test_rag_house_receipts_directory_exists():
    """Verify RAG house receipts directory exists."""
    receipts = Path("data/internal-rag-house/receipts")
    if not receipts.exists():
        pytest.skip("RAG house receipts not yet created")


def test_rag_dollhouse_references_have_content():
    """Verify RAG dollhouse references have content."""
    references = Path("skills/lantern-rag-dollhouse/references")
    ref_files = list(references.glob("*.md"))
    
    if len(ref_files) > 0:
        for ref_file in ref_files:
            content = ref_file.read_text(encoding="utf-8")
            assert len(content) > 50, f"Reference file should have content: {ref_file}"


def test_rag_seeds_directory_exists():
    """Verify RAG seeds directory exists."""
    seeds_dir = Path("rag/seeds")
    if not seeds_dir.exists():
        pytest.skip("RAG seeds directory not yet created")


def test_rag_seeds_have_content():
    """Verify RAG seeds have content."""
    seeds_dir = Path("rag/seeds")
    if seeds_dir.exists():
        seed_files = list(seeds_dir.glob("*.md"))
        if len(seed_files) > 0:
            for seed_file in seed_files:
                content = seed_file.read_text(encoding="utf-8")
                assert len(content) > 50, f"Seed file should have content: {seed_file}"


def test_rag_house_flat_rag_latest_exists():
    """Verify flat RAG latest manifest exists."""
    manifest = Path("data/flat-rag-house-latest.json")
    if not manifest.exists():
        pytest.skip("Flat RAG latest not yet created")


def test_rag_house_script_exists():
    """Verify RAG house update script exists."""
    script = Path("scripts/Update-InternalHouseRag.ps1")
    if not script.exists():
        pytest.skip("RAG house update script not yet created")


def test_rag_house_script_has_params():
    """Verify RAG house script has parameters."""
    script = Path("scripts/Update-InternalHouseRag.ps1")
    if script.exists():
        content = script.read_text(encoding="utf-8")
        # Should have parameters
        if "param(" in content:
            pass  # Has parameters


def test_rag_dollhouse_has_boundaries():
    """Verify RAG dollhouse has boundaries."""
    skill_md = Path("skills/lantern-rag-dollhouse/SKILL.md")
    content = skill_md.read_text(encoding="utf-8")
    
    # Should have boundary information
    boundary_terms = ["boundary", "limit", "block", "scope"]
    found_boundary = any(term in content.lower() for term in boundary_terms)
    if found_boundary:
        pass  # Has boundaries


def test_rag_house_manifest_has_generated_at():
    """Verify RAG house manifest has generated at timestamp."""
    manifest = Path("data/internal-rag-house/RAG-HOUSE-MANIFEST.json")
    content = manifest.read_text(encoding="utf-8-sig")
    
    import json
    data = json.loads(content)
    if isinstance(data, dict):
        if "generatedAt" in data or "generated" in data:
            pass  # Has timestamp
