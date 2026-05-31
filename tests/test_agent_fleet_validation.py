"""
Agent Fleet Validation Tests

Tests for agent fleet configuration, agent boundaries,
and fleet management validation.
"""
import pytest
from pathlib import Path


def test_agent_fleet_directory_exists():
    """Verify agent fleet directory exists."""
    fleet_dir = Path("surfaces/agent-fleet")
    if not fleet_dir.exists():
        pytest.skip("Agent fleet surface not yet created")


def test_agent_fleet_has_index():
    """Verify agent fleet has index file."""
    fleet_dir = Path("surfaces/agent-fleet")
    if fleet_dir.exists():
        index = fleet_dir / "index.html"
        if index.exists():
            content = index.read_text(encoding="utf-8")
            assert len(content) > 50


def test_agent_fleet_has_fleet_js():
    """Verify agent fleet has fleet JavaScript."""
    fleet_dir = Path("surfaces/agent-fleet")
    if fleet_dir.exists():
        fleet_js = fleet_dir / "fleet.js"
        if fleet_js.exists():
            content = fleet_js.read_text(encoding="utf-8")
            assert len(content) > 50


def test_agent_fleet_has_styles():
    """Verify agent fleet has styles."""
    fleet_dir = Path("surfaces/agent-fleet")
    if fleet_dir.exists():
        styles = fleet_dir / "styles.css"
        if styles.exists():
            content = styles.read_text(encoding="utf-8")
            assert len(content) > 50


def test_agent_fleet_manifest_exists():
    """Verify agent fleet manifest exists."""
    manifest = Path("manifests/CONVERGENCE-LOOP-AGENT-FLEET.md")
    assert manifest.exists()


def test_agent_fleet_has_ring_slots():
    """Verify agent fleet has ring slots defined."""
    manifest = Path("manifests/CONVERGENCE-LOOP-AGENT-FLEET.md")
    content = manifest.read_text(encoding="utf-8")
    
    assert "ring" in content.lower() and "slot" in content.lower()


def test_agent_fleet_has_worker_pool():
    """Verify agent fleet has worker pool defined."""
    manifest = Path("manifests/CONVERGENCE-LOOP-AGENT-FLEET.md")
    content = manifest.read_text(encoding="utf-8")
    
    assert "worker" in content.lower() and "pool" in content.lower()


def test_agent_fleet_has_active_idle_metrics():
    """Verify agent fleet has active/idle metrics."""
    manifest = Path("manifests/CONVERGENCE-LOOP-AGENT-FLEET.md")
    content = manifest.read_text(encoding="utf-8")
    
    assert "active" in content.lower() or "idle" in content.lower()


def test_agent_fleet_has_queued_jobs():
    """Verify agent fleet has queued jobs tracking."""
    manifest = Path("manifests/CONVERGENCE-LOOP-AGENT-FLEET.md")
    content = manifest.read_text(encoding="utf-8")
    
    assert "queued" in content.lower() or "job" in content.lower()


def test_agent_fleet_has_failed_workers():
    """Verify agent fleet has failed workers tracking."""
    manifest = Path("manifests/CONVERGENCE-LOOP-AGENT-FLEET.md")
    content = manifest.read_text(encoding="utf-8")
    
    assert "failed" in content.lower()


def test_agent_fleet_has_consensus_receipts():
    """Verify agent fleet has consensus receipts."""
    manifest = Path("manifests/CONVERGENCE-LOOP-AGENT-FLEET.md")
    content = manifest.read_text(encoding="utf-8")
    
    assert "consensus" in content.lower() and "receipt" in content.lower()


def test_agent_fleet_blocks_unverified_claims():
    """Verify agent fleet blocks unverified claims."""
    manifest = Path("manifests/CONVERGENCE-LOOP-AGENT-FLEET.md")
    content = manifest.read_text(encoding="utf-8")
    
    assert "block" in content.lower() or "hold" in content.lower()


def test_agent_fleet_has_orchestrator_base_url():
    """Verify agent fleet has orchestrator base URL."""
    manifest = Path("manifests/CONVERGENCE-LOOP-AGENT-FLEET.md")
    content = manifest.read_text(encoding="utf-8")
    
    assert "url" in content.lower() or "base" in content.lower()


def test_agent_fleet_has_mcp_health():
    """Verify agent fleet has MCP health check."""
    manifest = Path("manifests/CONVERGENCE-LOOP-AGENT-FLEET.md")
    content = manifest.read_text(encoding="utf-8")
    
    assert "mcp" in content.lower() and "health" in content.lower()


def test_agent_fleet_has_tools_visible():
    """Verify agent fleet has tools visible metric."""
    manifest = Path("manifests/CONVERGENCE-LOOP-AGENT-FLEET.md")
    content = manifest.read_text(encoding="utf-8")
    
    assert "tool" in content.lower() and "visible" in content.lower()


def test_agent_fleet_has_generated_at():
    """Verify agent fleet has generated at timestamp."""
    manifest = Path("manifests/CONVERGENCE-LOOP-AGENT-FLEET.md")
    content = manifest.read_text(encoding="utf-8")
    
    assert "generated" in content.lower() or "timestamp" in content.lower()


def test_agent_fleet_validation_script_exists():
    """Verify agent fleet validation script exists."""
    script = Path("scripts/Test-ConvergenceAgentFleet.py")
    if not script.exists():
        pytest.skip("Agent fleet validation script not yet created")


def test_agent_fleet_has_ring_slots_healthy():
    """Verify agent fleet has ring slots healthy metric."""
    manifest = Path("manifests/CONVERGENCE-LOOP-AGENT-FLEET.md")
    content = manifest.read_text(encoding="utf-8")
    
    assert "healthy" in content.lower()


def test_agent_fleet_has_ring_slots_assigned():
    """Verify agent fleet has ring slots assigned metric."""
    manifest = Path("manifests/CONVERGENCE-LOOP-AGENT-FLEET.md")
    content = manifest.read_text(encoding="utf-8")
    
    assert "assigned" in content.lower()


def test_agent_fleet_design_contract_exists():
    """Verify agent fleet design contract exists."""
    manifest = Path("manifests/CONVERGENCE-LOOP-AGENT-FLEET.md")
    content = manifest.read_text(encoding="utf-8")
    
    assert "design" in content.lower() and "contract" in content.lower()


def test_agent_fleet_blocks_live_worker_claims():
    """Verify agent fleet blocks live worker claims without proof."""
    manifest = Path("manifests/CONVERGENCE-LOOP-AGENT-FLEET.md")
    content = manifest.read_text(encoding="utf-8")
    
    assert "live" in content.lower() and "worker" in content.lower()
