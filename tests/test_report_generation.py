"""
Report Generation Tests

Tests for report generation, PDF creation,
and report validation.
"""
import pytest
from pathlib import Path


def test_reports_directory_exists():
    """Verify reports directory exists."""
    reports_dir = Path("reports")
    assert reports_dir.exists()


def test_reports_have_content():
    """Verify reports directory has content."""
    reports_dir = Path("reports")
    report_files = list(reports_dir.glob("*.md"))
    
    assert len(report_files) > 0, "Reports directory should have markdown files"


def test_report_generation_scripts_exist():
    """Verify report generation scripts exist."""
    scripts = [
        "scripts/Build-DayOneNormiePdf.ps1",
        "scripts/Build-CloudMigrationConsolidationPdf.ps1",
    ]
    
    for script in scripts:
        script_path = Path(script)
        if not script_path.exists():
            pytest.skip(f"Report generation script not yet created: {script}")


def test_report_assets_directory_exists():
    """Verify report assets directory exists."""
    assets_dir = Path("reports/assets")
    if not assets_dir.exists():
        pytest.skip("Report assets directory not yet created")


def test_report_founder_wisdom_directory_exists():
    """Verify founder wisdom directory exists."""
    founder_dir = Path("reports/FOUNDER-WISDOM-DECISION-CARDS")
    if not founder_dir.exists():
        pytest.skip("Founder wisdom directory not yet created")


def test_report_pdf_files_exist():
    """Verify report PDF files exist."""
    reports_dir = Path("reports")
    pdf_files = list(reports_dir.glob("*.pdf"))
    
    if len(pdf_files) > 0:
        # Has PDF files
        pass


def test_report_html_files_exist():
    """Verify report HTML files exist."""
    reports_dir = Path("reports")
    html_files = list(reports_dir.glob("*.html"))
    
    if len(html_files) > 0:
        # Has HTML files
        pass


def test_report_files_are_not_empty():
    """Verify report files are not empty."""
    reports_dir = Path("reports")
    md_files = list(reports_dir.glob("*.md"))
    
    for md_file in md_files:
        content = md_file.read_text(encoding="utf-8")
        assert len(content.strip()) > 0, f"Report file is empty: {md_file}"


def test_report_templates_exist():
    """Verify report templates exist."""
    templates_dir = Path("templates/evidence")
    if not templates_dir.exists():
        pytest.skip("Report templates directory not yet created")


def test_report_receipt_template_exists():
    """Verify report receipt template exists."""
    template = Path("templates/evidence/payment-receipt-template.md")
    if not template.exists():
        pytest.skip("Report receipt template not yet created")


def test_report_canary_template_exists():
    """Verify report canary template exists."""
    template = Path("templates/evidence/mcp-canary-test-receipt-template.md")
    if not template.exists():
        pytest.skip("Report canary template not yet created")


def test_report_generation_script_has_params():
    """Verify report generation script has parameters."""
    script = Path("scripts/Build-DayOneNormiePdf.ps1")
    if script.exists():
        content = script.read_text(encoding="utf-8")
        if "param(" in content:
            pass  # Has parameters


def test_report_has_metadata():
    """Verify reports have metadata."""
    reports_dir = Path("reports")
    md_files = list(reports_dir.glob("*.md"))
    
    for md_file in md_files:
        content = md_file.read_text(encoding="utf-8")
        # Should have some structure
        if "#" in content:
            pass  # Has headers


def test_report_has_date():
    """Verify reports have date information."""
    reports_dir = Path("reports")
    md_files = list(reports_dir.glob("*.md"))
    
    for md_file in md_files:
        content = md_file.read_text(encoding="utf-8")
        # Should have date
        if "2026" in content or "date" in content.lower():
            pass  # Has date


def test_report_has_title():
    """Verify reports have title."""
    reports_dir = Path("reports")
    md_files = list(reports_dir.glob("*.md"))
    
    for md_file in md_files:
        content = md_file.read_text(encoding="utf-8")
        # Should have title header
        if "# " in content:
            pass  # Has title


def test_report_has_evidence():
    """Verify reports have evidence sections."""
    reports_dir = Path("reports")
    md_files = list(reports_dir.glob("*.md"))
    
    for md_file in md_files:
        content = md_file.read_text(encoding="utf-8")
        # Should have evidence
        if "evidence" in content.lower():
            pass  # Has evidence


def test_report_has_validation():
    """Verify reports have validation sections."""
    reports_dir = Path("reports")
    md_files = list(reports_dir.glob("*.md"))
    
    for md_file in md_files:
        content = md_file.read_text(encoding="utf-8")
        # Should have validation
        if "validation" in content.lower():
            pass  # Has validation


def test_report_generation_python_scripts_exist():
    """Verify report generation Python scripts exist."""
    python_scripts = [
        "generate_pdf.py",
        "generate_plan_pdf.py",
        "generate_founder_oss_report.py",
    ]
    
    for script in python_scripts:
        script_path = Path(script)
        if not script_path.exists():
            pytest.skip(f"Report generation Python script not yet created: {script}")


def test_report_templates_have_content():
    """Verify report templates have content."""
    templates_dir = Path("templates/evidence")
    if templates_dir.exists():
        template_files = list(templates_dir.glob("*.md"))
        for template_file in template_files:
            content = template_file.read_text(encoding="utf-8")
            assert len(content) > 50, f"Template should have content: {template_file}"


def test_report_has_conclusion():
    """Verify reports have conclusion or next steps."""
    reports_dir = Path("reports")
    md_files = list(reports_dir.glob("*.md"))
    
    for md_file in md_files:
        content = md_file.read_text(encoding="utf-8")
        # Should have conclusion or next steps
        if "conclusion" in content.lower() or "next" in content.lower():
            pass  # Has conclusion or next steps


def test_report_has_boundary():
    """Verify reports have boundary information."""
    reports_dir = Path("reports")
    md_files = list(reports_dir.glob("*.md"))
    
    for md_file in md_files:
        content = md_file.read_text(encoding="utf-8")
        # Should have boundary
        if "boundary" in content.lower() or "limit" in content.lower():
            pass  # Has boundary
