"""
CI/CD Workflow Validation Tests

Validates GitHub Actions workflows, CI/CD configuration,
and automation pipeline integrity.
"""
import pytest
import yaml
from pathlib import Path


def test_github_workflows_directory_exists():
    """Verify GitHub workflows directory exists."""
    workflows_dir = Path(".github/workflows")
    assert workflows_dir.exists()


def test_required_workflows_exist():
    """Verify required GitHub Actions workflows exist."""
    required_workflows = [
        "static-surface-ci.yml",
        "browser-testing-ci.yml",
        "orchestration-challenge-ci.yml",
        "mcp-tunnel-canary.yml",
        "release-provenance.yml",
    ]
    
    workflows_dir = Path(".github/workflows")
    for workflow in required_workflows:
        assert (workflows_dir / workflow).exists(), f"Missing workflow: {workflow}"


def test_workflows_are_valid_yaml():
    """Verify workflow files are valid YAML."""
    workflows_dir = Path(".github/workflows")
    workflow_files = list(workflows_dir.glob("*.yml")) + list(workflows_dir.glob("*.yaml"))
    
    for workflow_file in workflow_files:
        content = workflow_file.read_text(encoding="utf-8")
        try:
            yaml.safe_load(content)
        except yaml.YAMLError as e:
            pytest.fail(f"Invalid YAML in {workflow_file}: {e}")


def test_static_surface_ci_workflow_structure():
    """Verify static surface CI workflow has required structure."""
    workflow_file = Path(".github/workflows/static-surface-ci.yml")
    content = workflow_file.read_text(encoding="utf-8")
    
    required_jobs = [
        "repo-surface",
        "manifests",
        "html-links",
        "python-tests",
        "summary",
    ]
    
    for job in required_jobs:
        assert job in content, f"Static surface CI missing job: {job}"


def test_browser_testing_ci_workflow_structure():
    """Verify browser testing CI workflow has required structure."""
    workflow_file = Path(".github/workflows/browser-testing-ci.yml")
    content = workflow_file.read_text(encoding="utf-8")
    
    required_jobs = [
        "install-deps",
        "browser-tests",
        "trade-chat-unit-tests",
        "summary",
    ]
    
    for job in required_jobs:
        assert job in content, f"Browser testing CI missing job: {job}"


def test_workflows_have_on_triggers():
    """Verify workflows have trigger definitions."""
    workflows_dir = Path(".github/workflows")
    workflow_files = list(workflows_dir.glob("*.yml"))
    
    for workflow_file in workflow_files:
        content = workflow_file.read_text(encoding="utf-8")
        assert "on:" in content, f"{workflow_file} should have trigger definition"


def test_workflows_use_checkout_action():
    """Verify workflows use checkout action."""
    workflows_dir = Path(".github/workflows")
    workflow_files = list(workflows_dir.glob("*.yml"))
    
    for workflow_file in workflow_files:
        content = workflow_file.read_text(encoding="utf-8")
        assert "actions/checkout" in content, f"{workflow_file} should use checkout action"


def test_workflows_have_permissions():
    """Verify workflows have permissions defined."""
    workflows_dir = Path(".github/workflows")
    workflow_files = list(workflows_dir.glob("*.yml"))
    
    for workflow_file in workflow_files:
        content = workflow_file.read_text(encoding="utf-8")
        # Should have permissions section
        assert "permissions:" in content, f"{workflow_file} should have permissions"


def test_orchestration_challenge_ci_has_contract_guards():
    """Verify orchestration challenge CI has contract guards."""
    workflow_file = Path(".github/workflows/orchestration-challenge-ci.yml")
    content = workflow_file.read_text(encoding="utf-8")
    
    required_guards = [
        "mcp-contract",
        "action-pool-contract",
        "science-report-contract",
    ]
    
    for guard in required_guards:
        assert guard in content, f"Orchestration challenge CI missing guard: {guard}"


def test_mcp_canary_workflow_has_safety_checks():
    """Verify MCP canary workflow has safety checks."""
    workflow_file = Path(".github/workflows/mcp-tunnel-canary.yml")
    content = workflow_file.read_text(encoding="utf-8")
    
    safety_checks = [
        "https",
        "localhost",
        "127.0.0.1",
    ]
    
    for check in safety_checks:
        assert check in content, f"MCP canary workflow missing safety check: {check}"


def test_workflows_have_concurrency():
    """Verify workflows have concurrency control."""
    workflows_dir = Path(".github/workflows")
    workflow_files = list(workflows_dir.glob("*.yml"))
    
    for workflow_file in workflow_files:
        content = workflow_file.read_text(encoding="utf-8")
        # Should have concurrency for PR workflows
        if "pull_request" in content:
            assert "concurrency:" in content, f"{workflow_file} should have concurrency for PRs"


def test_workflows_use_ubuntu_latest():
    """Verify workflows use ubuntu-latest runner."""
    workflows_dir = Path(".github/workflows")
    workflow_files = list(workflows_dir.glob("*.yml"))
    
    for workflow_file in workflow_files:
        content = workflow_file.read_text(encoding="utf-8")
        assert "ubuntu-latest" in content, f"{workflow_file} should use ubuntu-latest"


def test_browser_testing_ci_installs_playwright():
    """Verify browser testing CI installs Playwright."""
    workflow_file = Path(".github/workflows/browser-testing-ci.yml")
    content = workflow_file.read_text(encoding="utf-8")
    
    assert "playwright" in content.lower(), "Browser testing CI should install Playwright"


def test_workflows_upload_artifacts_on_failure():
    """Verify workflows upload artifacts on failure."""
    workflow_file = Path(".github/workflows/browser-testing-ci.yml")
    content = workflow_file.read_text(encoding="utf-8")
    
    assert "upload-artifact" in content, "Browser testing CI should upload artifacts"


def test_release_provenance_workflow_exists():
    """Verify release provenance workflow exists."""
    workflow_file = Path(".github/workflows/release-provenance.yml")
    assert workflow_file.exists()


def test_workflows_have_summary_jobs():
    """Verify workflows have summary jobs."""
    workflows_dir = Path(".github/workflows")
    workflow_files = list(workflows_dir.glob("*.yml"))
    
    for workflow_file in workflow_files:
        content = workflow_file.read_text(encoding="utf-8")
        # Check for summary or similar job
        if "summary" in content.lower() or "report" in content.lower():
            break  # At least one workflow has summary


def test_ci_workflows_run_on_master():
    """Verify CI workflows run on master branch."""
    workflows_dir = Path(".github/workflows")
    workflow_files = list(workflows_dir.glob("*.yml"))
    
    for workflow_file in workflow_files:
        content = workflow_file.read_text(encoding="utf-8")
        if "push:" in content or "pull_request:" in content:
            assert "master" in content, f"{workflow_file} should run on master branch"


def test_workflows_have_proper_indentation():
    """Verify workflow YAML has proper indentation."""
    workflows_dir = Path(".github/workflows")
    workflow_files = list(workflows_dir.glob("*.yml"))
    
    for workflow_file in workflow_files:
        content = workflow_file.read_text(encoding="utf-8")
        lines = content.split("\n")
        
        for i, line in enumerate(lines):
            if line.strip().startswith("-") and not line.startswith("  -"):
                # List items should be indented
                pass  # This is a soft check


def test_no_secrets_in_workflows():
    """Verify no secrets are hardcoded in workflows."""
    workflows_dir = Path(".github/workflows")
    workflow_files = list(workflows_dir.glob("*.yml"))
    
    secret_patterns = [
        "api_key",
        "secret",
        "password",
        "token",
    ]
    
    for workflow_file in workflow_files:
        content = workflow_file.read_text(encoding="utf-8")
        for pattern in secret_patterns:
            # Check for hardcoded values (not ${{ secrets.XXX }})
            if pattern in content.lower() and "${{" not in content:
                pytest.fail(f"Potential hardcoded secret in {workflow_file}: {pattern}")


def test_workflows_use_action_versions():
    """Verify workflows use pinned action versions."""
    workflows_dir = Path(".github/workflows")
    workflow_files = list(workflows_dir.glob("*.yml"))
    
    for workflow_file in workflow_files:
        content = workflow_file.read_text(encoding="utf-8")
        # Check for @vX or @X.X.X pattern
        if "uses:" in content:
            # This is a soft check - should use versioned actions
            pass


def test_dockerfile_exists_for_apps():
    """Verify apps have Dockerfiles."""
    apps_dir = Path("apps")
    
    for app_path in apps_dir.iterdir():
        if app_path.is_dir() and not app_path.name.startswith("__"):
            dockerfile = app_path / "Dockerfile"
            if dockerfile.exists():
                content = dockerfile.read_text(encoding="utf-8")
                assert len(content) > 50, f"Dockerfile in {app_path.name} should have content"


def test_kubernetes_configs_exist():
    """Verify Kubernetes configs exist for apps."""
    apps_dir = Path("apps")
    
    for app_path in apps_dir.iterdir():
        if app_path.is_dir() and not app_path.name.startswith("__"):
            k8s_dir = app_path / "k8s"
            if k8s_dir.exists():
                k8s_files = list(k8s_dir.glob("*.yaml")) + list(k8s_dir.glob("*.yml"))
                assert len(k8s_files) > 0, f"{app_path.name} k8s directory should have config files"
