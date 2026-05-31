from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"


def readme() -> str:
    return README.read_text(encoding="utf-8")


def test_readme_is_lantern_front_page_not_hff_dump() -> None:
    text = readme()
    forbidden = [
        "human-flourishing-frameworks",
        "human flourishing frameworks",
        "HFF Render",
        "onrender.com",
        "deploy branch for the Render mirror",
    ]
    assert [phrase for phrase in forbidden if phrase.lower() in text.lower()] == []
    assert "Lantern OS is the clean control plane" in text
    assert "No bulk promotion of legacy framework content" in text


def test_readme_has_no_common_mojibake_or_replacement_artifacts() -> None:
    text = readme()
    forbidden = ["\ufffd", "Ã", "Â", "â€", "â€œ", "â€�", "â€™", "â€“", "â€”"]
    assert [artifact for artifact in forbidden if artifact in text] == []


def test_readme_preserves_truth_boundaries_and_aws_bridge() -> None:
    text = readme()
    required = [
        "Truth boundary: local MCP status, dirty source worktrees, private folders, boot mutation, and live worker counts require operator-machine evidence",
        "Held local-only",
        "AWS-held",
        "AWS/service mirrors live in `manifests/cloud-mirrors.json`",
        "apps/lantern-garage/cloud-server.js",
        "apps/lantern-garage/Dockerfile",
        "No AWS URL is verified until `/`, `/api/health`, and `/api/cloud-mirrors` pass on that URL",
        "POST /api/command",
        "docs/LANTERN-COMMAND-ENTRYPOINT.md",
        "docs/EXECUTION-BOUNDARIES.md",
    ]
    assert [phrase for phrase in required if phrase not in text] == []


def test_readme_keeps_flat_document_shape() -> None:
    text = readme()
    ordered_headings = [
        "# Lantern OS",
        "## Simple Answer",
        "## What It Actually Does",
        "## Evidence / Source Discipline",
        "## Proven / Held / Local-Only",
        "## First Command",
    ]
    positions = [text.index(heading) for heading in ordered_headings]
    assert positions == sorted(positions)
