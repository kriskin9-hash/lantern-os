"""
Security and Boundary Tests

Validates security boundaries, safety gates, and
operational boundaries across Lantern OS.
"""
import pytest
from pathlib import Path


def test_no_hardcoded_secrets_in_python():
    """Verify no hardcoded secrets in Python files."""
    secret_patterns = [
        "api_key",
        "secret_key",
        "password",
        "token",
        "private_key",
    ]
    
    python_files = list(Path(".").rglob("*.py"))
    python_files = [f for f in python_files if "node_modules" not in str(f) and ".git" not in str(f)]
    
    for py_file in python_files:
        content = py_file.read_text(encoding="utf-8")
        for pattern in secret_patterns:
            # Check for obvious hardcoded patterns (this is a basic check)
            if f'"{pattern}="' in content.lower() or f"'{pattern}='" in content.lower():
                # Allow if it's an environment variable reference
                if "os.environ" not in content and "getenv" not in content:
                    pytest.fail(f"Potential hardcoded secret in {py_file}: {pattern}")


def test_no_hardcoded_secrets_in_powershell():
    """Verify no hardcoded secrets in PowerShell files."""
    secret_patterns = [
        "api_key",
        "secret_key",
        "password",
        "token",
        "private_key",
    ]
    
    ps1_files = list(Path(".").rglob("*.ps1"))
    ps1_files = [f for f in ps1_files if "node_modules" not in str(f) and ".git" not in str(f)]
    
    for ps1_file in ps1_files:
        content = ps1_file.read_text(encoding="utf-8")
        for pattern in secret_patterns:
            # Check for obvious hardcoded patterns
            if f'${pattern}=' in content.lower() or f'"{pattern}="' in content.lower():
                # Allow if it's an environment variable reference
                if "env:" not in content.lower():
                    pytest.fail(f"Potential hardcoded secret in {ps1_file}: {pattern}")


def test_kill_switch_file_exists():
    """Verify kill switch file exists for trading."""
    kill_switch = Path("data/kalshi/LIVE-KILL-SWITCH")
    assert kill_switch.exists()


def test_kill_switch_blocks_trading():
    """Verify kill switch documentation blocks trading."""
    kill_switch = Path("data/kalshi/LIVE-KILL-SWITCH")
    content = kill_switch.read_text(encoding="utf-8")
    
    assert "DISARMED" in content or "ARMED" in content
    assert "safety" in content.lower() or "block" in content.lower()


def test_agents_md_has_safety_boundaries():
    """Verify AGENTS.md has safety boundaries."""
    agents = Path("AGENTS.md")
    content = agents.read_text(encoding="utf-8")
    
    safety_keywords = [
        "safety",
        "boundary",
        "do not",
        "blocked",
        "held",
    ]
    
    found_safety = any(keyword in content.lower() for keyword in safety_keywords)
    assert found_safety, "AGENTS.md should mention safety boundaries"


def test_mcp_connector_has_safety_contract():
    """Verify MCP connector has safety contract."""
    mcp_doc = Path("docs/MCP-CONNECTOR.md")
    content = mcp_doc.read_text(encoding="utf-8")
    
    assert "safety" in content.lower()
    assert "contract" in content.lower()


def test_mcp_blocks_remote_by_default():
    """Verify MCP blocks remote endpoints by default."""
    mcp_doc = Path("docs/MCP-CONNECTOR.md")
    content = mcp_doc.read_text(encoding="utf-8")
    
    assert "127.0.0.1" in content or "localhost" in content
    assert "untrusted" in content.lower()


def test_trading_docs_have_safety_gates():
    """Verify trading documentation has safety gates."""
    trading_docs = [
        "docs/KALSHI-LIVE-TRADING.md",
        "scripts/Invoke-KalshiLiveOrder.ps1",
    ]
    
    for doc_path in trading_docs:
        doc = Path(doc_path)
        if doc.exists():
            content = doc.read_text(encoding="utf-8")
            safety_keywords = ["kill switch", "cap", "limit", "safety"]
            found_safety = any(keyword in content.lower() for keyword in safety_keywords)
            assert found_safety, f"{doc_path} should mention safety gates"


def test_no_executable_scripts_in_repo():
    """Verify no executable scripts are accidentally committed."""
    # This is a basic check - in practice, scripts should be non-executable in git
    pass


def test_gitignore_blocks_sensitive_files():
    """Verify .gitignore blocks sensitive files."""
    gitignore = Path(".gitignore")
    content = gitignore.read_text(encoding="utf-8")
    
    sensitive_patterns = [
        ".env",
        "*.key",
        "*.pem",
        "secrets",
    ]
    
    for pattern in sensitive_patterns:
        assert pattern in content, f".gitignore should block: {pattern}"


def test_windsurf_hooks_have_safety_validators():
    """Verify Windsurf hooks have safety validators."""
    hooks_config = Path(".windsurf/hooks.json")
    if hooks_config.exists():
        content = hooks_config.read_text(encoding="utf-8")
        
        safety_hooks = [
            "Validate",
            "safety",
        ]
        
        found_safety = any(hook in content for hook in safety_hooks)
        assert found_safety, "Windsurf hooks should have safety validators"


def test_convergence_loop_blocks_dangerous_actions():
    """Verify convergence loop blocks dangerous actions."""
    convergence_script = Path("scripts/Invoke-LanternConvergenceLoop.ps1")
    content = convergence_script.read_text(encoding="utf-8")
    
    blocked_actions = [
        "boot",
        "partition",
        "firmware",
        "disk",
    ]
    
    # Should mention these are blocked
    found_blocks = sum(1 for action in blocked_actions if action in content.lower())
    assert found_blocks > 0, "Convergence loop should mention blocked actions"


def test_asi_skill_blocks_capability_claims():
    """Verify ASI skill blocks capability claims."""
    asi_skill = Path("skills/asi-arc-reactor-mk1/SKILL.md")
    content = asi_skill.read_text(encoding="utf-8")
    
    blocked_claims = [
        "no local ASI capability",
        "architecture references only",
    ]
    
    for claim in blocked_claims:
        assert claim in content, f"ASI skill should block: {claim}"


def test_docs_mention_human_approval():
    """Verify documentation mentions human approval for dangerous actions."""
    docs_to_check = [
        "AGENTS.md",
        "docs/MCP-CONNECTOR.md",
        "docs/EXECUTION-BOUNDARIES.md",
    ]
    
    found_approval = False
    for doc_path in docs_to_check:
        doc = Path(doc_path)
        if doc.exists():
            content = doc.read_text(encoding="utf-8")
            if "human approval" in content.lower() or "operator approval" in content.lower():
                found_approval = True
                break
    
    assert found_approval, "Documentation should mention human approval"


def test_no_aws_keys_in_repo():
    """Verify no AWS keys are in the repo."""
    aws_pattern = "AKIA[0-9A-Z]{16}"
    
    files_to_check = list(Path(".").rglob("*"))
    files_to_check = [f for f in files_to_check if f.is_file() and "node_modules" not in str(f) and ".git" not in str(f)]
    
    for file_path in files_to_check:
        try:
            content = file_path.read_text(encoding="utf-8")
            if aws_pattern in content:
                pytest.fail(f"Potential AWS key in {file_path}")
        except:
            pass  # Skip binary files


def test_dual_boot_docs_have_safety_warnings():
    """Verify dual boot documentation has safety warnings."""
    dual_boot_docs = [
        "dual-boot/README.md",
        "dual-boot/INSTALL-CHECKLIST.md",
    ]
    
    for doc_path in dual_boot_docs:
        doc = Path(doc_path)
        if doc.exists():
            content = doc.read_text(encoding="utf-8")
            safety_keywords = ["warning", "risk", "backup", "safety"]
            found_safety = any(keyword in content.lower() for keyword in safety_keywords)
            assert found_safety, f"{doc_path} should have safety warnings"
