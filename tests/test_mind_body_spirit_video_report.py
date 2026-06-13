from pathlib import Path

import pytest

# Archived 2026-06-10 to D:\tmp\archive\repo-archive-2026-06-10\ — these tests
# validate the archived report's gates when a copy is present locally.
REPORT = Path('archive/reports-2026-06-04/MIND-BODY-SPIRIT-SHINE-VIDEO-CONVERGENCE.md')


def _report_text() -> str:
    if not REPORT.exists():
        pytest.skip(f"report archived to D:\\tmp\\archive (not in repo): {REPORT}")
    return REPORT.read_text(encoding='utf-8')


def test_mind_body_spirit_video_report_is_off_hold_with_publication_gates():
    text = _report_text()

    required_phrases = [
        'Status: validated candidate',
        'Move the video/report work off hold',
        'Publication Gate',
        'captions',
        'three-flashes-per-second',
        'no request for comments, names, photos, location, account signup, or personal data',
        'rollback',
    ]

    missing = [phrase for phrase in required_phrases if phrase not in text]
    assert missing == []


def test_mind_body_spirit_video_report_does_not_claim_public_release_ready():
    text = _report_text().lower()

    forbidden_claims = [
        'status: held',
        'status: public-release ready',
        'status: v1.0.0 ready',
    ]

    present = [phrase for phrase in forbidden_claims if phrase in text]
    assert present == []
