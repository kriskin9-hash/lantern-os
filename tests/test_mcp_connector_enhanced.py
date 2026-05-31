"""
Enhanced MCP Connector Tests

Tests for MCP connector validation, safety boundaries, and tool discovery.
Validates the full MCP suite including local endpoints, remote tunnel safety,
and tool descriptor verification.
"""
import json
import pytest
from pathlib import Path


def test_mcp_connector_script_exists():
    """Verify the MCP connector test script exists."""
    script_path = Path("scripts/Test-LanternMcpConnector.ps1")
    assert script_path.exists(), "MCP connector test script must exist"


def test_mcp_documentation_exists():
    """Verify MCP connector documentation exists."""
    doc_path = Path("docs/MCP-CONNECTOR.md")
    assert doc_path.exists(), "MCP connector documentation must exist"


def test_mcp_work_split_exists():
    """Verify MCP work split documentation exists."""
    doc_path = Path("manifests/MCP-WORK-SPLIT.md")
    assert doc_path.exists(), "MCP work split documentation must exist"


def test_mcp_safety_contract_anchors():
    """Verify MCP safety contract is documented."""
    doc_path = Path("docs/MCP-CONNECTOR.md")
    doc_text = doc_path.read_text(encoding="utf-8")
    
    required_anchors = [
        "Use `http://127.0.0.1:8787`",
        "Treat remote tunnels as untrusted",
        "List tools, inspect descriptors, verify parameters",
        "Do not run arbitrary shell through MCP",
        "Do not accept advertised capability as proof",
    ]
    
    for anchor in required_anchors:
        assert anchor in doc_text, f"Missing safety anchor: {anchor}"


def test_mcp_script_safety_checks():
    """Verify MCP connector script has safety checks."""
    script_path = Path("scripts/Test-LanternMcpConnector.ps1")
    script_text = script_path.read_text(encoding="utf-8")
    
    required_checks = [
        "$isLoopback",
        "-AllowRemote",
        "remote_endpoint_blocked",
        "loopbackOnlyDefault",
    ]
    
    for check in required_checks:
        assert check in script_text, f"Missing safety check: {check}"


def test_mcp_validation_json_path():
    """Verify MCP validation JSON path is documented."""
    doc_path = Path("docs/MCP-CONNECTOR.md")
    doc_text = doc_path.read_text(encoding="utf-8")
    
    assert "manifests/validation/MCP-CONNECTOR-LATEST.json" in doc_text


def test_mcp_evidence_classes_documented():
    """Verify MCP evidence classes are documented."""
    doc_path = Path("docs/MCP-CONNECTOR.md")
    doc_text = doc_path.read_text(encoding="utf-8")
    
    evidence_classes = [
        "local_verified",
        "github_metadata",
        "source_repo_evidence",
        "operator_asserted",
        "held",
    ]
    
    for cls in evidence_classes:
        assert cls in doc_text, f"Missing evidence class: {cls}"


def test_mcp_held_items_documented():
    """Verify MCP held items are documented."""
    doc_path = Path("docs/MCP-CONNECTOR.md")
    doc_text = doc_path.read_text(encoding="utf-8")
    
    assert "Current Held Items" in doc_text
    assert "Full local MCP JSON-RPC tool enumeration" in doc_text


def test_mcp_promotion_gate_documented():
    """Verify MCP promotion gate is documented."""
    doc_path = Path("docs/MCP-CONNECTOR.md")
    doc_text = doc_path.read_text(encoding="utf-8")
    
    assert "Promotion Gate" in doc_text
    assert "Test-LanternMcpConnector.ps1" in doc_text
    assert "convergence loop" in doc_text


def test_mcp_work_split_lanes():
    """Verify MCP work split lanes are documented."""
    doc_path = Path("manifests/MCP-WORK-SPLIT.md")
    if not doc_path.exists():
        pytest.skip("MCP work split documentation not yet created")
    
    doc_text = doc_path.read_text(encoding="utf-8")
    
    required_lanes = [
        "Split Lanes",
        "Private Dependency Boundary",
        "OS Review Gate",
        "No Bulk Remote Push Without Gate",
    ]
    
    for lane in required_lanes:
        assert lane in doc_text, f"Missing work split lane: {lane}"


def test_mcp_canary_workflow_exists():
    """Verify MCP canary workflow exists."""
    workflow_path = Path(".github/workflows/mcp-tunnel-canary.yml")
    assert workflow_path.exists(), "MCP canary workflow must exist"


def test_mcp_canary_workflow_safety():
    """Verify MCP canary workflow has safety checks."""
    workflow_path = Path(".github/workflows/mcp-tunnel-canary.yml")
    workflow_text = workflow_path.read_text(encoding="utf-8")
    
    assert "https" in workflow_text, "Canary must require HTTPS"
    assert "localhost" in workflow_text, "Canary must block localhost"
    assert "127.0.0.1" in workflow_text, "Canary must block loopback"


def test_mcp_hooks_configuration():
    """Verify Windsurf MCP hooks are configured."""
    hooks_path = Path(".windsurf/hooks.json")
    if not hooks_path.exists():
        pytest.skip("Windsurf hooks not yet configured")
    
    hooks_text = hooks_path.read_text(encoding="utf-8")
    
    required_hooks = [
        "pre_mcp_tool_use",
        "Validate-McpTool",
        "Log-McpToolUse",
    ]
    
    for hook in required_hooks:
        assert hook in hooks_text, f"Missing MCP hook: {hook}"


def test_mcp_validation_directory():
    """Verify MCP validation directory exists."""
    validation_dir = Path("manifests/validation")
    assert validation_dir.exists(), "Validation directory must exist"
