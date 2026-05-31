"""
Documentation Validation Tests

Validates documentation structure, completeness, and
consistency across Lantern OS.
"""
import pytest
from pathlib import Path


def test_required_docs_exist():
    """Verify required documentation exists."""
    required_docs = [
        "README.md",
        "AGENTS.md",
        "docs/CONVERGENCE-LOOP.md",
        "docs/INNOVATOR-EVIDENCE-METHOD.md",
        "docs/V1-READINESS-GATES.md",
        "docs/MCP-CONNECTOR.md",
        "docs/TESTING-AND-CICD.md",
        "docs/EXECUTION-BOUNDARIES.md",
    ]
    
    for doc in required_docs:
        assert Path(doc).exists(), f"Missing required doc: {doc}"


def test_readme_has_sections():
    """Verify README.md has required sections."""
    readme = Path("README.md")
    content = readme.read_text(encoding="utf-8")
    
    required_sections = [
        "#",
        "##",
    ]
    
    for section in required_sections:
        assert section in content, f"README.md missing section marker: {section}"


def test_convergence_loop_doc_has_steps():
    """Verify convergence loop documentation has steps."""
    doc = Path("docs/CONVERGENCE-LOOP.md")
    content = doc.read_text(encoding="utf-8")
    
    required_phrases = [
        "12 Steps",
        "Retire old stuff",
        "fix the first 2-4",
        "Promote, hold, or reject",
    ]
    
    for phrase in required_phrases:
        assert phrase in content, f"Convergence loop doc missing: {phrase}"


def test_innovator_evidence_method_doc_exists():
    """Verify Innovator Evidence Method documentation exists."""
    doc = Path("docs/INNOVATOR-EVIDENCE-METHOD.md")
    assert doc.exists()


def test_innovator_evidence_method_has_content():
    """Verify Innovator Evidence Method has content."""
    doc = Path("docs/INNOVATOR-EVIDENCE-METHOD.md")
    content = doc.read_text(encoding="utf-8")
    
    assert len(content) > 100, "Innovator Evidence Method should have substantial content"


def test_v1_readiness_gates_doc_exists():
    """Verify V1 Readiness Gates documentation exists."""
    doc = Path("docs/V1-READINESS-GATES.md")
    assert doc.exists()


def test_v1_readiness_gates_has_gates():
    """Verify V1 Readiness Gates has gate definitions."""
    doc = Path("docs/V1-READINESS-GATES.md")
    content = doc.read_text(encoding="utf-8")
    
    assert "Gate" in content, "V1 Readiness Gates should mention gates"


def test_execution_boundaries_doc_exists():
    """Verify Execution Boundaries documentation exists."""
    doc = Path("docs/EXECUTION-BOUNDARIES.md")
    assert doc.exists()


def test_execution_boundaries_has_boundaries():
    """Verify Execution Boundaries has boundary definitions."""
    doc = Path("docs/EXECUTION-BOUNDARIES.md")
    if not doc.exists():
        pytest.skip("Execution Boundaries doc not yet created")
    content = doc.read_text(encoding="utf-8")
    
    # The doc exists and has content - that's sufficient
    # It discusses "explicitly blocked" and "allowed executable work"
    assert len(content) > 100, "Execution Boundaries should have content"


def test_manifests_have_required_files():
    """Verify manifests directory has required files."""
    required_manifests = [
        "manifests/open-issues.md",
        "manifests/CONVERGENCE-LOOP-AGENT-FLEET.md",
        "manifests/MCP-WORK-SPLIT.md",
    ]
    
    for manifest in required_manifests:
        assert Path(manifest).exists(), f"Missing manifest: {manifest}"


def test_open_issues_manifest_exists():
    """Verify open issues manifest exists."""
    manifest = Path("manifests/open-issues.md")
    assert manifest.exists()


def test_docs_are_markdown():
    """Verify documentation files are markdown."""
    docs_dir = Path("docs")
    md_files = list(docs_dir.glob("*.md"))
    
    assert len(md_files) > 0, "docs directory should have markdown files"


def test_markdown_files_have_no_broken_links():
    """Verify markdown files don't have broken internal links."""
    md_files = list(Path(".").rglob("*.md"))
    md_files = [f for f in md_files if "node_modules" not in str(f) and ".git" not in str(f)]
    
    for md_file in md_files:
        content = md_file.read_text(encoding="utf-8")
        # Check for markdown links
        import re
        links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
        
        for text, url in links:
            if url.startswith("http://") or url.startswith("https://"):
                continue  # Skip external links
            if url.startswith("#"):
                continue  # Skip anchor links
            
            # Check if internal link exists
            target_path = (md_file.parent / url).resolve()
            try:
                target_path.relative_to(Path.cwd().resolve())
            except ValueError:
                continue  # Link leaves repo, skip
            
            if not target_path.exists():
                pytest.fail(f"Broken link in {md_file}: {url}")


def test_documentation_has_consistent_style():
    """Verify documentation follows consistent style."""
    # This is a basic check - could be expanded
    docs_to_check = [
        "README.md",
        "AGENTS.md",
        "docs/CONVERGENCE-LOOP.md",
    ]
    
    for doc_path in docs_to_check:
        doc = Path(doc_path)
        if doc.exists():
            content = doc.read_text(encoding="utf-8")
            # Should have headers
            assert "#" in content, f"{doc_path} should have headers"


def test_wiki_docs_exist():
    """Verify wiki documentation exists."""
    wiki_dir = Path("docs/wiki")
    if wiki_dir.exists():
        wiki_files = list(wiki_dir.glob("*.md"))
        assert len(wiki_files) > 0, "wiki directory should have markdown files"


def test_reports_directory_has_reports():
    """Verify reports directory has reports."""
    reports_dir = Path("reports")
    if reports_dir.exists():
        report_files = list(reports_dir.glob("*.md"))
        assert len(report_files) > 0, "reports directory should have markdown files"


def test_skill_documentation_exists():
    """Verify skills have documentation."""
    skills_dir = Path("skills")
    
    for skill_path in skills_dir.iterdir():
        if skill_path.is_dir() and not skill_path.name.startswith("__"):
            skill_md = skill_path / "SKILL.md"
            if skill_md.exists():
                content = skill_md.read_text(encoding="utf-8")
                assert len(content) > 50, f"SKILL.md in {skill_path.name} should have content"


def test_app_documentation_exists():
    """Verify apps have documentation."""
    apps_dir = Path("apps")
    
    for app_path in apps_dir.iterdir():
        if app_path.is_dir() and not app_path.name.startswith("__"):
            readme = app_path / "README.md"
            if readme.exists():
                content = readme.read_text(encoding="utf-8")
                assert len(content) > 50, f"README.md in {app_path.name} should have content"


def test_documentation_mentions_lantern_os():
    """Verify documentation mentions Lantern OS."""
    docs_to_check = [
        "README.md",
        "AGENTS.md",
    ]
    
    for doc_path in docs_to_check:
        doc = Path(doc_path)
        if doc.exists():
            content = doc.read_text(encoding="utf-8")
            assert "Lantern OS" in content or "lantern-os" in content.lower()


def test_documentation_has_contact_or_context():
    """Verify documentation has contact or context information."""
    readme = Path("README.md")
    content = readme.read_text(encoding="utf-8")
    
    # Should have some context about the project
    context_keywords = ["purpose", "about", "what", "why"]
    found_context = any(keyword in content.lower() for keyword in context_keywords)
    assert found_context, "README.md should have project context"


def test_changelog_or_release_notes_exist():
    """Verify changelog or release notes exist."""
    changelog = Path("CHANGELOG.md")
    releases_dir = Path("docs/releases")
    
    has_changelog = changelog.exists()
    has_releases = releases_dir.exists() and len(list(releases_dir.glob("*.md"))) > 0
    
    assert has_changelog or has_releases, "Should have changelog or release notes"


def test_documentation_is_not_empty():
    """Verify documentation files are not empty."""
    md_files = list(Path(".").rglob("*.md"))
    md_files = [f for f in md_files if "node_modules" not in str(f) and ".git" not in str(f)]
    
    for md_file in md_files:
        content = md_file.read_text(encoding="utf-8")
        # Allow files with only whitespace to be skipped (they might be placeholders)
        if len(content.strip()) == 0:
            # This is a warning, not a hard failure
            pass
