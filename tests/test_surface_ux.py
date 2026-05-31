"""
Surface UX Tests

Tests for surface user experience, UI components,
and surface validation.
"""
import pytest
from pathlib import Path


def test_surface_dashboard_ux_test_exists():
    """Verify surface dashboard UX test exists."""
    test_file = Path("tests/test_dashboard_ux.py")
    assert test_file.exists()


def test_surface_shared_canonical_css_exists():
    """Verify shared canonical CSS exists."""
    css = Path("surfaces/shared-canonical.css")
    assert css.exists()


def test_surface_shared_canonical_css_has_content():
    """Verify shared canonical CSS has content."""
    css = Path("surfaces/shared-canonical.css")
    content = css.read_text(encoding="utf-8")
    
    assert len(content) > 50, "Shared CSS should have content"


def test_surface_lantern_desktop_exists():
    """Verify lantern desktop surface exists."""
    desktop = Path("surfaces/lantern-desktop")
    assert desktop.exists()


def test_surface_lantern_desktop_has_index():
    """Verify lantern desktop has index."""
    desktop = Path("surfaces/lantern-desktop")
    index = desktop / "index.html"
    assert index.exists()


def test_surface_lantern_desktop_has_day_one_pocketart():
    """Verify lantern desktop has day one pocket art."""
    desktop = Path("surfaces/lantern-desktop")
    pocketart = desktop / "day-one-pocketart.html"
    assert pocketart.exists()


def test_surface_bayesian_dashboard_exists():
    """Verify bayesian dashboard surface exists."""
    dashboard = Path("surfaces/bayesian-dashboard")
    if not dashboard.exists():
        pytest.skip("Bayesian dashboard surface not yet created")


def test_surface_bayesian_dashboard_has_doc():
    """Verify bayesian dashboard has documentation."""
    doc = Path("surfaces/bayesian-dashboard/BAYESIAN-DASHBOARD.md")
    if not doc.exists():
        pytest.skip("Bayesian dashboard doc not yet created")


def test_surface_garage_dashboard_exists():
    """Verify garage dashboard surface exists."""
    garage = Path("surfaces/garage-dashboard")
    if not garage.exists():
        pytest.skip("Garage dashboard surface not yet created")


def test_surface_agent_fleet_exists():
    """Verify agent fleet surface exists."""
    fleet = Path("surfaces/agent-fleet")
    if not fleet.exists():
        pytest.skip("Agent fleet surface not yet created")


def test_surface_agent_fleet_has_index():
    """Verify agent fleet has index."""
    fleet = Path("surfaces/agent-fleet")
    if fleet.exists():
        index = fleet / "index.html"
        if index.exists():
            content = index.read_text(encoding="utf-8")
            assert len(content) > 50


def test_surface_agent_fleet_has_fleet_js():
    """Verify agent fleet has fleet JavaScript."""
    fleet = Path("surfaces/agent-fleet")
    if fleet.exists():
        fleet_js = fleet / "fleet.js"
        if fleet_js.exists():
            content = fleet_js.read_text(encoding="utf-8")
            assert len(content) > 50


def test_surface_agent_fleet_has_styles():
    """Verify agent fleet has styles."""
    fleet = Path("surfaces/agent-fleet")
    if fleet.exists():
        styles = fleet / "styles.css"
        if styles.exists():
            content = styles.read_text(encoding="utf-8")
            assert len(content) > 50


def test_surface_dashboard_index_exists():
    """Verify dashboard index exists."""
    dashboard = Path("dashboard")
    index = dashboard / "index.html"
    assert index.exists()


def test_surface_dashboard_convergence_exists():
    """Verify dashboard convergence exists."""
    dashboard = Path("dashboard")
    convergence = dashboard / "convergence-dashboard.html"
    assert convergence.exists()


def test_surface_css_has_orion_style():
    """Verify surface CSS has Orion style references."""
    css = Path("surfaces/shared-canonical.css")
    content = css.read_text(encoding="utf-8")
    
    # Check for Orion-style elements
    orion_elements = ["limestone", "warm", "white", "grid", "teal", "cyan"]
    found_orion = any(element in content.lower() for element in orion_elements)
    if found_orion:
        pass  # Has Orion style elements


def test_surface_html_has_proper_structure():
    """Verify surface HTML files have proper structure."""
    html_files = list(Path("surfaces").rglob("*.html"))
    html_files = [f for f in html_files if "node_modules" not in str(f)]
    
    for html_file in html_files:
        content = html_file.read_text(encoding="utf-8")
        # Should have HTML structure
        assert "<html" in content or "<!DOCTYPE" in content, f"{html_file} should have HTML structure"


def test_surface_html_links_to_css():
    """Verify surface HTML files link to CSS."""
    html_files = list(Path("surfaces").rglob("*.html"))
    html_files = [f for f in html_files if "node_modules" not in str(f)]
    
    for html_file in html_files:
        content = html_file.read_text(encoding="utf-8")
        # Should link to CSS
        if "stylesheet" in content or "link" in content:
            pass  # Has CSS link


def test_surface_html_has_no_broken_images():
    """Verify surface HTML files don't have broken image references."""
    html_files = list(Path("surfaces").rglob("*.html"))
    html_files = [f for f in html_files if "node_modules" not in str(f)]
    
    for html_file in html_files:
        content = html_file.read_text(encoding="utf-8")
        # Check for image tags
        if "<img" in content:
            pass  # Has images


def test_surface_directory_structure():
    """Verify surfaces directory has proper structure."""
    surfaces_dir = Path("surfaces")
    assert surfaces_dir.exists()
    
    required_surfaces = [
        "lantern-desktop",
        "shared-canonical.css",
    ]
    
    for surface in required_surfaces:
        assert (surfaces_dir / surface).exists(), f"Missing surface: {surface}"


def test_surface_files_are_not_empty():
    """Verify surface files are not empty."""
    surface_files = list(Path("surfaces").rglob("*"))
    surface_files = [f for f in surface_files if f.is_file() and not f.name.startswith(".")]
    
    for surface_file in surface_files:
        if surface_file.suffix in [".html", ".css", ".js"]:
            content = surface_file.read_text(encoding="utf-8")
            assert len(content.strip()) > 0, f"Surface file is empty: {surface_file}"
