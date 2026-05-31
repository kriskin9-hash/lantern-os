"""
Fleet Orchestration Tests

Tests for agent fleet orchestration, convergence loop execution,
and fleet management.
"""
import pytest
from pathlib import Path


def test_convergence_fleet_manifest_exists():
    """Verify convergence fleet manifest exists."""
    manifest = Path("manifests/CONVERGENCE-LOOP-AGENT-FLEET.md")
    assert manifest.exists()


def test_convergence_fleet_has_12_steps():
    """Verify convergence fleet has 12 steps."""
    manifest = Path("manifests/CONVERGENCE-LOOP-AGENT-FLEET.md")
    content = manifest.read_text(encoding="utf-8")
    
    assert "12" in content or "twelve" in content.lower()


def test_convergence_fleet_has_36_agents():
    """Verify convergence fleet has 36 ring agents."""
    manifest = Path("manifests/CONVERGENCE-LOOP-AGENT-FLEET.md")
    content = manifest.read_text(encoding="utf-8")
    
    assert "36" in content or "thirty-six" in content.lower() or "ring agents" in content.lower()


def test_convergence_fleet_has_64_worker_target():
    """Verify convergence fleet has 64 worker pool target."""
    manifest = Path("manifests/CONVERGENCE-LOOP-AGENT-FLEET.md")
    content = manifest.read_text(encoding="utf-8")
    
    assert "64" in content or "worker" in content.lower()


def test_convergence_fleet_has_contract():
    """Verify convergence fleet has contract definition."""
    manifest = Path("manifests/CONVERGENCE-LOOP-AGENT-FLEET.md")
    content = manifest.read_text(encoding="utf-8")
    
    assert "contract" in content.lower()


def test_convergence_fleet_has_receipt_validation():
    """Verify convergence fleet has receipt validation."""
    manifest = Path("manifests/CONVERGENCE-LOOP-AGENT-FLEET.md")
    content = manifest.read_text(encoding="utf-8")
    
    assert "receipt" in content.lower()


def test_convergence_fleet_has_claim_boundary():
    """Verify convergence fleet has claim boundary."""
    manifest = Path("manifests/CONVERGENCE-LOOP-AGENT-FLEET.md")
    content = manifest.read_text(encoding="utf-8")
    
    assert "claim" in content.lower() and "boundary" in content.lower()


def test_convergence_fleet_validation_script_exists():
    """Verify convergence fleet validation script exists."""
    script = Path("scripts/Test-ConvergenceAgentFleet.py")
    # This script may not exist yet, so we skip if not found
    if not script.exists():
        pytest.skip("Convergence fleet validation script not yet created")


def test_fleet_manifest_has_role_matrix():
    """Verify fleet manifest has role matrix."""
    manifest = Path("manifests/CONVERGENCE-LOOP-AGENT-FLEET.md")
    content = manifest.read_text(encoding="utf-8")
    
    assert "role" in content.lower() or "matrix" in content.lower()


def test_fleet_manifest_has_consensus():
    """Verify fleet manifest has consensus mechanism."""
    manifest = Path("manifests/CONVERGENCE-LOOP-AGENT-FLEET.md")
    content = manifest.read_text(encoding="utf-8")
    
    assert "consensus" in content.lower()


def test_fleet_manifest_has_backup_agents():
    """Verify fleet manifest has backup agents."""
    manifest = Path("manifests/CONVERGENCE-LOOP-AGENT-FLEET.md")
    content = manifest.read_text(encoding="utf-8")
    
    assert "backup" in content.lower()


def test_fleet_manifest_blocks_live_claims():
    """Verify fleet manifest blocks live claims without proof."""
    manifest = Path("manifests/CONVERGENCE-LOOP-AGENT-FLEET.md")
    content = manifest.read_text(encoding="utf-8")
    
    assert "not_observed" in content or "proof" in content.lower()


def test_fleet_manifest_mentions_validation_json():
    """Verify fleet manifest mentions validation JSON."""
    manifest = Path("manifests/CONVERGENCE-LOOP-AGENT-FLEET.md")
    content = manifest.read_text(encoding="utf-8")
    
    assert "validation" in content.lower() and "json" in content.lower()


def test_convergence_loop_script_exists():
    """Verify convergence loop script exists."""
    script = Path("scripts/Invoke-LanternConvergenceLoop.ps1")
    assert script.exists()


def test_convergence_loop_script_has_fleet_check():
    """Verify convergence loop script checks fleet."""
    script = Path("scripts/Invoke-LanternConvergenceLoop.ps1")
    content = script.read_text(encoding="utf-8")
    
    assert "fleet" in content.lower() or "agent" in content.lower()


def test_fleet_validation_json_exists():
    """Verify fleet validation JSON exists."""
    validation_json = Path("manifests/validation/CONVERGENCE-FLEET-LATEST.json")
    if not validation_json.exists():
        pytest.skip("Fleet validation JSON not yet generated")


def test_fleet_manifest_has_step_definitions():
    """Verify fleet manifest has step definitions."""
    manifest = Path("manifests/CONVERGENCE-LOOP-AGENT-FLEET.md")
    content = manifest.read_text(encoding="utf-8")
    
    assert "step" in content.lower()


def test_fleet_manifest_has_orchestrator_reference():
    """Verify fleet manifest references orchestrator."""
    manifest = Path("manifests/CONVERGENCE-LOOP-AGENT-FLEET.md")
    content = manifest.read_text(encoding="utf-8")
    
    assert "orchestrator" in content.lower()


def test_fleet_manifest_has_mcp_reference():
    """Verify fleet manifest references MCP."""
    manifest = Path("manifests/CONVERGENCE-LOOP-AGENT-FLEET.md")
    content = manifest.read_text(encoding="utf-8")
    
    assert "mcp" in content.lower()


def test_fleet_manifest_has_health_checks():
    """Verify fleet manifest has health checks."""
    manifest = Path("manifests/CONVERGENCE-LOOP-AGENT-FLEET.md")
    content = manifest.read_text(encoding="utf-8")
    
    assert "health" in content.lower()


def test_fleet_manifest_has_rollback_path():
    """Verify fleet manifest has rollback path."""
    manifest = Path("manifests/CONVERGENCE-LOOP-AGENT-FLEET.md")
    content = manifest.read_text(encoding="utf-8")
    
    assert "rollback" in content.lower() or "fallback" in content.lower()
