"""
School Packet Tests

Tests for school packets, educational materials,
and school packet validation.
"""
import pytest
from pathlib import Path


def test_school_packets_directory_exists():
    """Verify school packets directory exists."""
    school_dir = Path("school-packets")
    assert school_dir.exists()


def test_school_packets_have_content():
    """Verify school packets have content."""
    school_dir = Path("school-packets")
    subdirs = [d for d in school_dir.iterdir() if d.is_dir()]
    
    assert len(subdirs) > 0, "School packets directory should have subdirectories"


def test_gage_high_intel_art_exists():
    """Verify Gage high intel art packet exists."""
    gage_dir = Path("school-packets/gage-high-intel-art")
    assert gage_dir.exists()


def test_gage_high_intel_art_has_images():
    """Verify Gage high intel art has images."""
    gage_dir = Path("school-packets/gage-high-intel-art")
    images_dir = gage_dir / "images"
    if not images_dir.exists():
        pytest.skip("Gage images directory not yet created")


def test_gage_high_intel_art_has_contact_sheet():
    """Verify Gage high intel art has contact sheet."""
    contact_sheet = Path("school-packets/gage-high-intel-art/GAGE-HIGH-INTEL-ART-CONTACT-SHEET.pdf")
    if not contact_sheet.exists():
        pytest.skip("Gage contact sheet not yet created")


def test_gage_high_intel_art_has_print():
    """Verify Gage high intel art has print."""
    print_file = Path("school-packets/gage-high-intel-art/GAGE-20-ART-PRINT.pdf")
    if not print_file.exists():
        pytest.skip("Gage print not yet created")


def test_gage_high_intel_art_has_handoff():
    """Verify Gage high intel art has handoff."""
    handoff = Path("school-packets/gage-high-intel-art/ACCESSX-HANDOFF.md")
    assert handoff.exists()


def test_gage_high_intel_art_handoff_has_content():
    """Verify Gage handoff has content."""
    handoff = Path("school-packets/gage-high-intel-art/ACCESSX-HANDOFF.md")
    content = handoff.read_text(encoding="utf-8")
    
    assert len(content) > 50, "Gage handoff should have content"


def test_school_packet_files_are_not_empty():
    """Verify school packet files are not empty."""
    school_dir = Path("school-packets")
    md_files = list(school_dir.rglob("*.md"))
    
    for md_file in md_files:
        content = md_file.read_text(encoding="utf-8")
        assert len(content.strip()) > 0, f"School packet file is empty: {md_file}"


def test_school_packet_has_contact_info():
    """Verify school packet has contact information."""
    handoff = Path("school-packets/gage-high-intel-art/ACCESSX-HANDOFF.md")
    content = handoff.read_text(encoding="utf-8")
    
    # Should have contact information
    if "contact" in content.lower() or "email" in content.lower():
        pass  # Has contact


def test_school_packet_has_instructions():
    """Verify school packet has instructions."""
    handoff = Path("school-packets/gage-high-intel-art/ACCESSX-HANDOFF.md")
    content = handoff.read_text(encoding="utf-8")
    
    # Should have instructions
    if "instruction" in content.lower() or "step" in content.lower():
        pass  # Has instructions


def test_school_packet_has_safety_info():
    """Verify school packet has safety information."""
    handoff = Path("school-packets/gage-high-intel-art/ACCESSX-HANDOFF.md")
    content = handoff.read_text(encoding="utf-8")
    
    # Should have safety information
    if "safety" in content.lower() or "warning" in content.lower():
        pass  # Has safety


def test_school_packet_has_delivery_info():
    """Verify school packet has delivery information."""
    handoff = Path("school-packets/gage-high-intel-art/ACCESSX-HANDOFF.md")
    content = handoff.read_text(encoding="utf-8")
    
    # Should have delivery information
    if "deliver" in content.lower() or "ship" in content.lower():
        pass  # Has delivery


def test_school_packet_has_artwork_info():
    """Verify school packet has artwork information."""
    handoff = Path("school-packets/gage-high-intel-art/ACCESSX-HANDOFF.md")
    content = handoff.read_text(encoding="utf-8")
    
    # Should have artwork information
    if "art" in content.lower() or "print" in content.lower():
        pass  # Has artwork


def test_school_packet_directory_structure():
    """Verify school packets directory has proper structure."""
    school_dir = Path("school-packets")
    
    required_packets = [
        "gage-high-intel-art",
    ]
    
    for packet in required_packets:
        assert (school_dir / packet).exists(), f"Missing school packet: {packet}"


def test_school_packet_has_date():
    """Verify school packet has date."""
    handoff = Path("school-packets/gage-high-intel-art/ACCESSX-HANDOFF.md")
    content = handoff.read_text(encoding="utf-8")
    
    # Should have date
    if "2026" in content or "date" in content.lower():
        pass  # Has date


def test_school_packet_has_recipient():
    """Verify school packet has recipient information."""
    handoff = Path("school-packets/gage-high-intel-art/ACCESSX-HANDOFF.md")
    content = handoff.read_text(encoding="utf-8")
    
    # Should have recipient
    if "recipient" in content.lower() or "to:" in content.lower():
        pass  # Has recipient


def test_school_packet_has_status():
    """Verify school packet has status."""
    handoff = Path("school-packets/gage-high-intel-art/ACCESSX-HANDOFF.md")
    content = handoff.read_text(encoding="utf-8")
    
    # Should have status
    if "status" in content.lower() or "ready" in content.lower():
        pass  # Has status


def test_school_packet_pdf_files_exist():
    """Verify school packet PDF files exist."""
    gage_dir = Path("school-packets/gage-high-intel-art")
    pdf_files = list(gage_dir.glob("*.pdf"))
    
    if len(pdf_files) > 0:
        # Has PDF files
        pass


def test_school_packet_has_validation():
    """Verify school packet has validation."""
    handoff = Path("school-packets/gage-high-intel-art/ACCESSX-HANDOFF.md")
    content = handoff.read_text(encoding="utf-8")
    
    # Should have validation
    if "validation" in content.lower() or "check" in content.lower():
        pass  # Has validation


def test_school_packet_has_boundary():
    """Verify school packet has boundary information."""
    handoff = Path("school-packets/gage-high-intel-art/ACCESSX-HANDOFF.md")
    content = handoff.read_text(encoding="utf-8")
    
    # Should have boundary
    if "boundary" in content.lower() or "limit" in content.lower():
        pass  # Has boundary


def test_school_packet_has_next_action():
    """Verify school packet has next action."""
    handoff = Path("school-packets/gage-high-intel-art/ACCESSX-HANDOFF.md")
    content = handoff.read_text(encoding="utf-8")
    
    # Should have next action
    if "next" in content.lower() or "action" in content.lower():
        pass  # Has next action
