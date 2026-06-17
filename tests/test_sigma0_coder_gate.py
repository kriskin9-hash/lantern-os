from src.sigma0_coder_gate import (
    REQUIRED_SECTIONS,
    assess_coder_output,
    build_pre_generation_gate,
    normalize_evidence,
)


def test_pre_generation_gate_caps_confidence_without_evidence():
    gate = build_pre_generation_gate()

    assert gate["grounded"] is False
    assert gate["max_confidence"] == 0.3
    assert gate["required_sections"] == list(REQUIRED_SECTIONS)
    assert "file reads" in gate["missing_evidence"]


def test_pre_generation_gate_allows_full_confidence_with_evidence():
    gate = build_pre_generation_gate(
        [
            {
                "claim": "Issue #628 requires evidence-backed local coder output.",
                "source": "GitHub issue #628",
                "confidence": 1.0,
            }
        ]
    )

    assert gate["grounded"] is True
    assert gate["max_confidence"] == 1.0
    assert gate["missing_evidence"] == []
    assert gate["evidence"][0]["source"] == "GitHub issue #628"


def test_normalize_evidence_clamps_confidence_and_accepts_strings():
    records = normalize_evidence(
        [
            {"claim": "Too high", "source": "test", "confidence": 9},
            {"claim": "Too low", "source": "test", "confidence": -4},
            "String evidence",
        ]
    )

    assert records[0]["confidence"] == 1.0
    assert records[1]["confidence"] == 0.0
    assert records[2]["source"] == "user-supplied"


def test_assess_coder_output_passes_when_required_sections_present():
    result = assess_coder_output(
        """
Claim: Add a structural gate.
Evidence: tests/test_sigma0_coder_gate.py covers required behavior.
Confidence: 82%
Source: local test file.
Verification: run python -m pytest tests/test_sigma0_coder_gate.py -q
"""
    )

    assert result["passed"] is True
    assert result["missing_sections"] == []
    assert result["max_confidence"] == 82


def test_assess_coder_output_fails_when_sections_missing():
    result = assess_coder_output("Looks good to me. Confidence: 90%")

    assert result["passed"] is False
    assert "claim" in result["missing_sections"]
    assert "evidence" in result["missing_sections"]
    assert "verification" in result["missing_sections"]
