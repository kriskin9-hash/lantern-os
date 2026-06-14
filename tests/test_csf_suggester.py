"""Tests for csf_agent.suggester — issue #383."""
import tempfile
from pathlib import Path

import pytest

from csf_agent.suggester import generate_spec, write_spec

_ISSUE = {
    "number": 999,
    "title": "csf-agent: test module — unit test fixture",
    "body": (
        "## Purpose\nTest fixture for suggester tests.\n\n"
        "## Acceptance Criteria\n"
        "- [ ] generate_spec returns markdown string\n"
        "- [ ] write_spec creates file\n"
        "- [ ] does not overwrite existing\n\n"
        "## Test command\n```bash\npython -m pytest tests/test_csf_suggester.py -q\n```"
    ),
    "labels": ["p1", "dream-journal"],
    "url": "https://github.com/alex-place/lantern-os/issues/999",
    "createdAt": "2026-06-13T00:00:00Z",
}


def test_generate_spec_returns_string():
    md = generate_spec(_ISSUE, score=0.75)
    assert isinstance(md, str)
    assert len(md) > 0


def test_generate_spec_contains_title():
    md = generate_spec(_ISSUE, score=0.75)
    assert "test module" in md


def test_generate_spec_contains_number():
    md = generate_spec(_ISSUE, score=0.75)
    assert "999" in md


def test_generate_spec_contains_score():
    md = generate_spec(_ISSUE, score=0.75)
    assert "0.75" in md


def test_generate_spec_contains_checklist_items():
    md = generate_spec(_ISSUE, score=0.75)
    assert "generate_spec" in md or "write_spec" in md or "does not overwrite" in md


def test_write_spec_creates_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = write_spec(_ISSUE, score=0.75, ingest_dir=Path(tmpdir))
        assert path.exists()
        content = path.read_text(encoding="utf-8")
        assert "999" in content


def test_write_spec_filename_contains_issue_number():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = write_spec(_ISSUE, score=0.75, ingest_dir=Path(tmpdir))
        assert "999" in path.name


def test_write_spec_no_overwrite():
    with tempfile.TemporaryDirectory() as tmpdir:
        p1 = write_spec(_ISSUE, score=0.75, ingest_dir=Path(tmpdir))
        original_mtime = p1.stat().st_mtime
        p2 = write_spec(_ISSUE, score=0.99, ingest_dir=Path(tmpdir))
        assert p1 == p2
        assert p2.stat().st_mtime == original_mtime
