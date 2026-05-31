"""
Repository Structure Tests

Validates the Lantern OS repository structure, required files,
and organizational boundaries.
"""
import pytest
from pathlib import Path


def test_root_directory_exists():
    """Verify root directory structure."""
    root = Path(".")
    assert root.exists()


def test_required_top_level_files():
    """Verify required top-level files exist."""
    required_files = [
        "README.md",
        "AGENTS.md",
        ".gitignore",
        ".gitattributes",
    ]
    for file in required_files:
        assert Path(file).exists(), f"Missing required file: {file}"


def test_required_directories():
    """Verify required directories exist."""
    required_dirs = [
        "docs",
        "scripts",
        "tests",
        "skills",
        "manifests",
        "apps",
        "data",
        "reports",
        "surfaces",
    ]
    for dir_name in required_dirs:
        assert Path(dir_name).exists(), f"Missing required directory: {dir_name}"


def test_docs_directory_structure():
    """Verify docs directory has required structure."""
    docs_dir = Path("docs")
    assert docs_dir.exists()
    
    required_docs = [
        "CONVERGENCE-LOOP.md",
        "INNOVATOR-EVIDENCE-METHOD.md",
        "V1-READINESS-GATES.md",
        "MCP-CONNECTOR.md",
        "TESTING-AND-CICD.md",
    ]
    for doc in required_docs:
        assert (docs_dir / doc).exists(), f"Missing required doc: {doc}"


def test_scripts_directory_structure():
    """Verify scripts directory has required structure."""
    scripts_dir = Path("scripts")
    assert scripts_dir.exists()
    
    required_scripts = [
        "Invoke-LanternConvergenceLoop.ps1",
        "Invoke-LanternAutomationTestSuite.ps1",
        "Test-LanternMcpConnector.ps1",
        "Test-BrowserAutomation.ps1",
    ]
    for script in required_scripts:
        assert (scripts_dir / script).exists(), f"Missing required script: {script}"


def test_manifests_directory_structure():
    """Verify manifests directory has required structure."""
    manifests_dir = Path("manifests")
    assert manifests_dir.exists()
    
    required_manifests = [
        "open-issues.md",
        "CONVERGENCE-LOOP-AGENT-FLEET.md",
        "MCP-WORK-SPLIT.md",
    ]
    for manifest in required_manifests:
        assert (manifests_dir / manifest).exists(), f"Missing required manifest: {manifest}"


def test_validation_directory_exists():
    """Verify validation directory exists."""
    validation_dir = Path("manifests/validation")
    assert validation_dir.exists()


def test_evidence_directory_exists():
    """Verify evidence directory exists."""
    evidence_dir = Path("manifests/evidence")
    assert evidence_dir.exists()


def test_skills_directory_structure():
    """Verify skills directory has required structure."""
    skills_dir = Path("skills")
    assert skills_dir.exists()
    
    # Check for key skills
    key_skills = [
        "asi-arc-reactor-mk1",
        "trade",
        "lantern-rag-dollhouse",
    ]
    for skill in key_skills:
        assert (skills_dir / skill).exists(), f"Missing key skill: {skill}"


def test_apps_directory_structure():
    """Verify apps directory has required structure."""
    apps_dir = Path("apps")
    assert apps_dir.exists()
    
    # Check for key apps
    key_apps = [
        "lantern-trade-chat",
        "lantern-garage",
    ]
    for app in key_apps:
        assert (apps_dir / app).exists(), f"Missing key app: {app}"


def test_data_directory_structure():
    """Verify data directory has required structure."""
    data_dir = Path("data")
    assert data_dir.exists()
    
    # Check for key data directories
    key_data = [
        "kalshi",
        "arc-reactor",
    ]
    for data in key_data:
        assert (data_dir / data).exists(), f"Missing key data directory: {data}"


def test_github_workflows_exist():
    """Verify GitHub Actions workflows exist."""
    workflows_dir = Path(".github/workflows")
    assert workflows_dir.exists()
    
    required_workflows = [
        "static-surface-ci.yml",
        "browser-testing-ci.yml",
        "orchestration-challenge-ci.yml",
        "mcp-tunnel-canary.yml",
    ]
    for workflow in required_workflows:
        assert (workflows_dir / workflow).exists(), f"Missing workflow: {workflow}"


def test_windsurf_configuration_exists():
    """Verify Windsurf configuration exists."""
    windsurf_dir = Path(".windsurf")
    assert windsurf_dir.exists()
    
    assert (windsurf_dir / "hooks.json").exists()
    assert (windsurf_dir / "workflows").exists()


def test_gitignore_exists():
    """Verify .gitignore has sensible defaults."""
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


def test_no_secrets_in_repo():
    """Verify no obvious secret files are committed."""
    secret_patterns = [
        ".env",
        "*.key",
        "*.pem",
        "secrets",
        "credentials",
    ]
    
    for pattern in secret_patterns:
        matches = list(Path(".").rglob(pattern))
        # Filter out node_modules and .git
        matches = [m for m in matches if "node_modules" not in str(m) and ".git" not in str(m)]
        assert len(matches) == 0, f"Found potential secret file matching {pattern}: {matches}"


def test_readme_exists_and_has_content():
    """Verify README.md exists and has meaningful content."""
    readme = Path("README.md")
    assert readme.exists()
    
    content = readme.read_text(encoding="utf-8")
    assert len(content) > 100, "README.md should have substantial content"
    assert "Lantern OS" in content, "README.md should mention Lantern OS"


def test_agents_md_exists():
    """Verify AGENTS.md exists and has agent instructions."""
    agents = Path("AGENTS.md")
    assert agents.exists()
    
    content = agents.read_text(encoding="utf-8")
    assert len(content) > 100, "AGENTS.md should have substantial content"
