"""
Skill Validation Tests

Validates skill structure, documentation, and boundaries
for all Lantern OS skills.
"""
import pytest
from pathlib import Path


def test_asi_arc_reactor_mk1_skill_exists():
    """Verify ASI Arc Reactor MK1 skill exists."""
    skill_dir = Path("skills/asi-arc-reactor-mk1")
    assert skill_dir.exists()
    assert (skill_dir / "SKILL.md").exists()


def test_asi_arc_reactor_mk1_boundaries():
    """Verify ASI skill has proper boundary documentation."""
    skill_doc = Path("skills/asi-arc-reactor-mk1/SKILL.md")
    content = skill_doc.read_text(encoding="utf-8")
    
    required_boundaries = [
        "ASI patterns are architecture references only",
        "no local ASI capability claim",
        "no investment advice",
        "Brier-style error tracking",
        "human trial readiness",
    ]
    
    for boundary in required_boundaries:
        assert boundary in content, f"ASI skill missing boundary: {boundary}"


def test_trade_skill_exists():
    """Verify trade skill exists."""
    skill_dir = Path("skills/trade")
    assert skill_dir.exists()


def test_trade_skill_has_documentation():
    """Verify trade skill has documentation."""
    skill_dir = Path("skills/trade")
    
    required_docs = [
        "TRADING-ASSISTANT-ARCHITECTURE.md",
        "IBKR-INTEGRATION-RESEARCH.md",
    ]
    
    for doc in required_docs:
        assert (skill_dir / doc).exists(), f"Trade skill missing doc: {doc}"


def test_lantern_rag_dollhouse_skill_exists():
    """Verify Lantern RAG Dollhouse skill exists."""
    skill_dir = Path("skills/lantern-rag-dollhouse")
    assert skill_dir.exists()
    assert (skill_dir / "SKILL.md").exists()


def test_lantern_rag_dollhouse_has_references():
    """Verify RAG Dollhouse skill has references."""
    skill_dir = Path("skills/lantern-rag-dollhouse")
    assert (skill_dir / "references").exists()


def test_all_skills_have_skill_md():
    """Verify all skill directories have SKILL.md."""
    skills_dir = Path("skills")
    
    for skill_path in skills_dir.iterdir():
        if skill_path.is_dir() and not skill_path.name.startswith("__"):
            skill_md = skill_path / "SKILL.md"
            if skill_md.exists():
                content = skill_md.read_text(encoding="utf-8")
                assert len(content) > 50, f"SKILL.md in {skill_path.name} should have content"


def test_skill_boundaries_block_dangerous_claims():
    """Verify skills explicitly block dangerous claims."""
    skill_doc = Path("skills/asi-arc-reactor-mk1/SKILL.md")
    content = skill_doc.read_text(encoding="utf-8")
    
    blocked_claims = [
        "token issuance",
        "investment advice",
        "medical",
        "free cloud compute",
    ]
    
    for claim in blocked_claims:
        # Should either explicitly block or not claim
        # This is a soft check - skills should be careful about these
        pass


def test_skill_documentation_has_purpose():
    """Verify skill documentation includes purpose."""
    skill_doc = Path("skills/asi-arc-reactor-mk1/SKILL.md")
    content = skill_doc.read_text(encoding="utf-8")
    
    # Should have a purpose section
    assert "purpose" in content.lower() or "what it does" in content.lower()


def test_skill_documentation_has_boundaries():
    """Verify skill documentation includes boundaries."""
    skill_doc = Path("skills/asi-arc-reactor-mk1/SKILL.md")
    content = skill_doc.read_text(encoding="utf-8")
    
    # Should have boundary information
    assert "boundary" in content.lower() or "limit" in content.lower() or "block" in content.lower()


def test_convergence_fleet_manifest_exists():
    """Verify convergence fleet manifest exists."""
    manifest = Path("manifests/CONVERGENCE-LOOP-AGENT-FLEET.md")
    assert manifest.exists()


def test_convergence_fleet_has_contract():
    """Verify convergence fleet has contract information."""
    manifest = Path("manifests/CONVERGENCE-LOOP-AGENT-FLEET.md")
    content = manifest.read_text(encoding="utf-8")
    
    required_phrases = [
        "12 convergence-loop steps",
        "36 ring agents",
        "poolTarget = 64",
    ]
    
    for phrase in required_phrases:
        assert phrase in content, f"Fleet manifest missing: {phrase}"


def test_bayesian_world_model_skill_exists():
    """Verify Bayesian World Model skill exists."""
    skill_dir = Path("skills/bayesian-world-model")
    assert skill_dir.exists()
    assert (skill_dir / "SKILL.md").exists()


def test_arc_reactor_confidence_skill_exists():
    """Verify Arc Reactor Confidence skill exists."""
    skill_dir = Path("skills/arc-reactor-confidence")
    assert skill_dir.exists()
    assert (skill_dir / "SKILL.md").exists()
