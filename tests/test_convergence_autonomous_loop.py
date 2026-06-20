"""Tests for the autonomous convergence loop (issue #592).

These lock the four acceptance criteria from issue #592:
  1. The loop runs end-to-end on 3 consecutive issues with no human intervention.
  2. Overall confidence >= 0.85 on each convergence record.
  3. The evidence trail is written to data/convergence-autonomous-work.jsonl.
  4. Benchmark scores are written per-run to data/agi-benchmark.jsonl.

Outputs are redirected to a temp dir; grounding (git grep) still runs against the
real repository, so the scores under test are genuinely measured.
"""

import json
import subprocess

import pytest

from convergence.objects import ConvergenceRecord
from convergence_autonomous_loop import (
    CONFIDENCE_THRESHOLD,
    DIMENSIONS,
    AutonomousConvergenceLoop,
)


def _git_grounding_available() -> bool:
    """True if ``git grep`` can ground against this checkout."""
    try:
        r = subprocess.run(
            ["git", "grep", "-l", "-I", "-i", "--fixed-strings", "--", "convergence"],
            cwd=AutonomousConvergenceLoop().repo_root,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except Exception:
        return False
    return r.returncode == 0 and bool(r.stdout.strip())


grounding = pytest.mark.skipif(
    not _git_grounding_available(),
    reason="git grep grounding unavailable; confidence scores cannot be measured",
)


@pytest.fixture(scope="module")
def run_result(tmp_path_factory):
    """Run the loop once over the 3-issue fixture into an isolated temp dir."""
    out = tmp_path_factory.mktemp("acl-out")
    issues = AutonomousConvergenceLoop.load_issues(source="fixture", count=3)
    assert len(issues) == 3, "fixture must provide 3 issues"
    loop = AutonomousConvergenceLoop(out_dir=out)
    summary = loop.run(issues)
    work = [json.loads(x) for x in loop.work_log.read_text(encoding="utf-8").splitlines() if x.strip()]
    bench = [json.loads(x) for x in loop.benchmark_log.read_text(encoding="utf-8").splitlines() if x.strip()]
    return {"summary": summary, "loop": loop, "work": work, "bench": bench, "out": out}


# --- criterion 1: 3 consecutive issues, no human intervention -----------------
def test_processes_three_issues(run_result):
    assert run_result["summary"]["issue_count"] == 3
    assert len(run_result["work"]) == 3


def test_no_human_intervention(run_result):
    assert run_result["summary"]["benchmark"]["human_intervention"] is False
    for pi in run_result["summary"]["per_issue"]:
        assert pi["human_intervention"] is False
    for rec in run_result["work"]:
        assert rec["result"]["human_intervention"] is False


# --- criterion 2: overall confidence >= 0.85 per record -----------------------
@grounding
def test_each_record_above_threshold(run_result):
    for rec in run_result["work"]:
        assert rec["confidence"] >= CONFIDENCE_THRESHOLD, (
            f"record {rec['id']} confidence {rec['confidence']} < {CONFIDENCE_THRESHOLD}"
        )
        assert rec["result"]["above_threshold"] is True


@grounding
def test_benchmark_reports_all_above_threshold(run_result):
    assert run_result["bench"][0]["all_records_above_threshold"] is True


@grounding
def test_acceptance_flags(run_result):
    acc = run_result["summary"]["acceptance"]
    assert acc["ran_3_consecutive_no_human"] is True
    assert acc["all_overall_confidence_ge_threshold"] is True
    assert acc["evidence_trail_written"] is True
    assert acc["benchmark_updated"] is True


# --- criterion 3: evidence trail = canonical ConvergenceRecords ---------------
def test_work_records_are_canonical_convergence_records(run_result):
    canonical_keys = {
        "id", "hypothesis", "evidence_ids", "result", "confidence",
        "reasoner", "timestamp", "verified", "verification_notes",
    }
    for rec in run_result["work"]:
        assert canonical_keys.issubset(rec.keys())
        # Must reconstruct into the canonical dataclass (schema contract).
        obj = ConvergenceRecord(
            id=rec["id"], hypothesis=rec["hypothesis"], evidence_ids=rec["evidence_ids"],
            result=rec["result"], confidence=rec["confidence"], reasoner=rec["reasoner"],
            verified=rec["verified"], verification_notes=rec["verification_notes"],
        )
        assert obj.id == rec["id"]


def test_every_record_carries_claim_evidence_confidence_source(run_result):
    """LANTERN-VERIFY: every record must carry [claim, evidence, confidence, source]."""
    for rec in run_result["work"]:
        res = rec["result"]
        assert res["claim"], "claim missing"
        assert isinstance(res["evidence"], list) and res["evidence"], "evidence missing"
        assert res["source"], "source missing"
        assert isinstance(rec["confidence"], (int, float)), "confidence missing"


def test_dimensions_present_and_in_range(run_result):
    for rec in run_result["work"]:
        dims = rec["result"]["dimensions"]
        assert set(dims.keys()) == set(DIMENSIONS)
        for name, score in dims.items():
            assert 0.0 <= score <= 1.0, f"{name}={score} out of range"


# --- criterion 4: benchmark scores per run ------------------------------------
def test_one_benchmark_record_per_run(run_result):
    assert len(run_result["bench"]) == 1
    b = run_result["bench"][0]
    assert b["schema"] == "agi-benchmark/v1"
    assert b["issue_count"] == 3
    assert set(b["dimensions"].keys()) == set(DIMENSIONS)
    for name, d in b["dimensions"].items():
        assert {"measured", "target", "delta"}.issubset(d.keys())
        assert abs(d["delta"] - (d["measured"] - d["target"])) < 1e-6
    assert {"measured", "target", "delta"}.issubset(b["overall_sigma0"].keys())


def test_benchmark_overall_is_mean_of_records(run_result):
    b = run_result["bench"][0]
    recs = run_result["work"]
    expected = round(sum(r["confidence"] for r in recs) / len(recs), 4)
    assert abs(b["overall_sigma0"]["measured"] - expected) < 1e-3


# --- append-only behavior (memory is never overwritten) -----------------------
def test_jsonl_is_append_only(tmp_path):
    out = tmp_path / "out"
    issues = AutonomousConvergenceLoop.load_issues(source="fixture", count=3)
    AutonomousConvergenceLoop(out_dir=out).run(issues)
    AutonomousConvergenceLoop(out_dir=out).run(issues)
    work = [x for x in (out / "convergence-autonomous-work.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    bench = [x for x in (out / "agi-benchmark.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    assert len(work) == 6, "second run must append, not overwrite, work records"
    assert len(bench) == 2, "each run must append exactly one benchmark record"


def test_fixture_issues_are_consecutive():
    issues = AutonomousConvergenceLoop.load_issues(source="fixture", count=3)
    ids = [i["id"] for i in issues]
    assert ids == sorted(ids)
    assert ids[-1] - ids[0] == 2, "fixture should be 3 consecutive issue numbers"
