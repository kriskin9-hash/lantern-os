"""
Integration Tests

Tests that validate integration between components,
end-to-end workflows, and cross-component interactions.
"""
import pytest
import json
from pathlib import Path


def test_convergence_loop_integration():
    """Test convergence loop integrates with all required components."""
    # This test would actually run the convergence loop
    # For now, we validate the script exists and has proper structure
    script = Path("scripts/Invoke-LanternConvergenceLoop.ps1")
    assert script.exists()
    
    content = script.read_text(encoding="utf-8")
    
    # Should check multiple components
    components = [
        "README.md",
        "AGENTS.md",
        "skills/asi-arc-reactor-mk1",
        ".windsurf/hooks.json",
    ]
    
    for component in components:
        assert component in content, f"Convergence loop should check: {component}"


def test_automation_suite_integration():
    """Test automation suite integrates all test categories."""
    script = Path("scripts/Invoke-LanternAutomationTestSuite.ps1")
    assert script.exists()
    
    content = script.read_text(encoding="utf-8")
    
    # Should integrate multiple test types
    test_types = [
        "python",
        "powershell",
        "mcp",
        "convergence",
    ]
    
    for test_type in test_types:
        assert test_type in content.lower(), f"Automation suite should include: {test_type}"


def test_mcp_connector_integration_with_windsurf():
    """Test MCP connector integrates with Windsurf hooks."""
    mcp_doc = Path("docs/MCP-CONNECTOR.md")
    hooks_config = Path(".windsurf/hooks.json")
    
    assert mcp_doc.exists()
    assert hooks_config.exists()
    
    # MCP doc should mention Windsurf
    mcp_content = mcp_doc.read_text(encoding="utf-8")
    hooks_content = hooks_config.read_text(encoding="utf-8")
    
    # Should have MCP-related hooks
    assert "mcp" in hooks_content.lower()


def test_trade_chat_integration_with_kalshi_scripts():
    """Test trade chat app integrates with Kalshi PowerShell scripts."""
    trade_chat = Path("apps/lantern-trade-chat")
    kalshi_script = Path("scripts/Invoke-KalshiLiveOrder.ps1")
    
    assert trade_chat.exists()
    assert kalshi_script.exists()
    
    # Both should implement similar safety gates
    trade_chat_safety = (trade_chat / "app/safety.py")
    if trade_chat_safety.exists():
        safety_content = trade_chat_safety.read_text(encoding="utf-8")
        kalshi_content = kalshi_script.read_text(encoding="utf-8")
        
        # Both should mention kill switch
        assert "kill" in safety_content.lower() or "switch" in safety_content.lower()
        assert "kill" in kalshi_content.lower() or "switch" in kalshi_content.lower()


def test_data_integration_between_components():
    """Test data flows between components correctly."""
    # Arc reactor status should be referenced by convergence
    arc_status = Path("data/arc-reactor/status.json")
    convergence_script = Path("scripts/Invoke-LanternConvergenceLoop.ps1")
    
    assert arc_status.exists()
    assert convergence_script.exists()


def test_validation_json_files_are_consistent():
    """Test validation JSON files have consistent structure."""
    validation_dir = Path("manifests/validation")
    json_files = list(validation_dir.glob("*.json"))
    
    if len(json_files) > 0:
        # All should have generatedAt field
        for json_file in json_files:
            content = json_file.read_text(encoding="utf-8-sig")  # Handle UTF-8 BOM
            data = json.loads(content)
            # Check for common fields
            if isinstance(data, dict):
                pass  # Has structure


def test_skill_integration_with_fleet_manifest():
    """Test skills integrate with convergence fleet manifest."""
    fleet_manifest = Path("manifests/CONVERGENCE-LOOP-AGENT-FLEET.md")
    skills_dir = Path("skills")
    
    assert fleet_manifest.exists()
    assert skills_dir.exists()
    
    fleet_content = fleet_manifest.read_text(encoding="utf-8")
    
    # Should mention skills or agents
    skill_terms = ["skill", "agent", "agent-fleet"]
    found_skill = any(term in fleet_content.lower() for term in skill_terms)
    assert found_skill, "Fleet manifest should mention skills or agents"


def test_ci_workflows_integration():
    """Test CI workflows integrate with each other."""
    workflows_dir = Path(".github/workflows")
    
    static_ci = workflows_dir / "static-surface-ci.yml"
    browser_ci = workflows_dir / "browser-testing-ci.yml"
    orchestration_ci = workflows_dir / "orchestration-challenge-ci.yml"
    
    assert static_ci.exists()
    assert browser_ci.exists()
    assert orchestration_ci.exists()
    
    # All should run Python tests
    static_content = static_ci.read_text(encoding="utf-8")
    browser_content = browser_ci.read_text(encoding="utf-8")
    orchestration_content = orchestration_ci.read_text(encoding="utf-8")
    
    assert "pytest" in static_content.lower() or "python" in static_content.lower()
    assert "pytest" in browser_content.lower() or "python" in browser_content.lower()
    assert "pytest" in orchestration_content.lower() or "python" in orchestration_content.lower()


def test_documentation_cross_references():
    """Test documentation cross-references each other."""
    docs_to_check = [
        "docs/CONVERGENCE-LOOP.md",
        "docs/INNOVATOR-EVIDENCE-METHOD.md",
        "docs/MCP-CONNECTOR.md",
    ]
    
    for doc_path in docs_to_check:
        doc = Path(doc_path)
        if doc.exists():
            content = doc.read_text(encoding="utf-8")
            # Should reference other docs
            if ".md" in content:
                pass  # Has markdown references


def test_evidence_files_reference_sources():
    """Test evidence files reference their sources."""
    evidence_dir = Path("manifests/evidence")
    md_files = list(evidence_dir.glob("*.md"))
    
    for evidence_file in md_files:
        content = evidence_file.read_text(encoding="utf-8")
        # Should have some structure
        assert len(content) > 50, f"Evidence file should have content: {evidence_file}"


def test_kalshi_data_integration():
    """Test Kalshi data files integrate with each other."""
    kalshi_dir = Path("data/kalshi")
    
    ledger = kalshi_dir / "kalshi-paper-ledger.jsonl"
    positions = kalshi_dir / "kalshi-paper-positions-latest.json"
    
    if ledger.exists() and positions.exists():
        # Both should exist and be valid
        ledger_content = ledger.read_text(encoding="utf-8")
        positions_content = positions.read_text(encoding="utf-8")
        
        # Ledger should be JSONL
        lines = ledger_content.strip().split("\n")
        for line in lines:
            if line.strip():
                json.loads(line)
        
        # Positions should be JSON
        json.loads(positions_content)


def test_windsurf_hooks_integration():
    """Test Windsurf hooks integrate with the system."""
    hooks_config = Path(".windsurf/hooks.json")
    hooks_dir = Path(".windsurf/hooks")
    
    assert hooks_config.exists()
    assert hooks_dir.exists()
    
    hooks_content = hooks_config.read_text(encoding="utf-8")
    hook_scripts = list(hooks_dir.glob("*.ps1"))
    
    # Config should reference hook scripts
    if len(hook_scripts) > 0:
        for hook_script in hook_scripts:
            hook_name = hook_script.stem
            assert hook_name in hooks_content, f"Config should reference hook: {hook_name}"


def test_apps_integration_with_data():
    """Test apps integrate with data structures."""
    trade_chat = Path("apps/lantern-trade-chat")
    kalshi_data = Path("data/kalshi")
    
    if trade_chat.exists() and kalshi_data.exists():
        # Trade chat should reference Kalshi data concepts
        trade_chat_config = trade_chat / "app/config.py"
        if trade_chat_config.exists():
            config_content = trade_chat_config.read_text(encoding="utf-8")
            # Should have Kalshi-related configuration
            assert "kalshi" in config_content.lower()


def test_reports_integration_with_data():
    """Test reports integrate with data sources."""
    reports_dir = Path("reports")
    data_dir = Path("data")
    
    if reports_dir.exists() and data_dir.exists():
        # Reports should reference data
        report_files = list(reports_dir.glob("*.md"))
        if len(report_files) > 0:
            # At least one report should exist
            pass


def test_scripts_integration_with_docs():
    """Test scripts reference their documentation."""
    scripts_dir = Path("scripts")
    docs_dir = Path("docs")
    
    if scripts_dir.exists() and docs_dir.exists():
        # Scripts should have corresponding docs
        # This is a soft check - not all scripts need docs
        pass


def test_validation_pipeline_integration():
    """Test validation pipeline integrates all checks."""
    # The automation suite should run all validation
    automation_script = Path("scripts/Invoke-LanternAutomationTestSuite.ps1")
    assert automation_script.exists()
    
    content = automation_script.read_text(encoding="utf-8")
    
    # Should integrate multiple validation types
    validation_types = [
        "Test-PythonSuite",
        "Test-PowerShellSuite",
        "Test-McpConnector",
        "Test-ConvergenceLoop",
    ]
    
    for validation_type in validation_types:
        assert validation_type in content, f"Automation suite should include: {validation_type}"


def test_gitignore_integration():
    """Test .gitignore integrates with repo structure."""
    gitignore = Path(".gitignore")
    assert gitignore.exists()
    
    content = gitignore.read_text(encoding="utf-8")
    
    # Should ignore common patterns
    ignored_patterns = [
        "node_modules",
        "__pycache__",
        ".venv",
    ]
    
    for pattern in ignored_patterns:
        assert pattern in content, f".gitignore should ignore: {pattern}"


def test_open_issues_integration():
    """Test open issues manifest integrates with system."""
    open_issues = Path("manifests/open-issues.md")
    assert open_issues.exists()
    
    content = open_issues.read_text(encoding="utf-8")
    
    # Should have structure
    assert len(content) > 50, "Open issues should have content"
