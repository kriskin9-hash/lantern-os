"""Tests for csf_agent.scorer — issue #382."""
from datetime import datetime, timezone

import pytest

from csf_agent.embedder import CSFEmbedder
from csf_agent.scorer import score_issues

_NOW = datetime.now(timezone.utc).isoformat()


def _issue(number, labels=None, title="", body="", created_at=None):
    return {
        "number": number,
        "title": title,
        "body": body or "",
        "labels": labels or [],
        "url": f"https://github.com/test/repo/issues/{number}",
        "createdAt": created_at or _NOW,
    }


@pytest.fixture(scope="module")
def emb():
    return CSFEmbedder()


def test_score_adds_score_field(emb):
    issues = [_issue(1, labels=["p0", "dream-journal"])]
    ranked = score_issues(issues, emb)
    assert "score" in ranked[0]
    assert isinstance(ranked[0]["score"], float)


def test_p0_beats_p1(emb):
    issues = [
        _issue(10, labels=["p1", "dream-journal"]),
        _issue(20, labels=["p0", "dream-journal"]),
    ]
    ranked = score_issues(issues, emb)
    assert ranked[0]["number"] == 20


def test_dream_journal_beats_unlabeled(emb):
    issues = [
        _issue(1, labels=[]),
        _issue(2, labels=["dream-journal"]),
    ]
    ranked = score_issues(issues, emb)
    assert ranked[0]["number"] == 2


def test_recency_bonus(emb):
    old = "2020-01-01T00:00:00Z"
    issues = [
        _issue(1, labels=["p1"], created_at=old),
        _issue(2, labels=["p1"], created_at=_NOW),
    ]
    ranked = score_issues(issues, emb)
    assert ranked[0]["number"] == 2


def test_tie_breaking_by_number(emb):
    """Equal scores → lowest issue number first."""
    issues = [
        _issue(50, labels=[]),
        _issue(10, labels=[]),
        _issue(30, labels=[]),
    ]
    ranked = score_issues(issues, emb)
    numbers = [r["number"] for r in ranked]
    assert numbers == sorted(numbers)


def test_empty_input(emb):
    assert score_issues([], emb) == []


def test_sorted_descending(emb):
    issues = [
        _issue(1, labels=["p2"]),
        _issue(2, labels=["p0", "dream-journal"]),
        _issue(3, labels=["p1"]),
    ]
    ranked = score_issues(issues, emb)
    scores = [r["score"] for r in ranked]
    assert scores == sorted(scores, reverse=True)
