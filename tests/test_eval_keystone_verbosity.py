"""Lock eval_keystone bytes-per-correct (Gate F) — issue #851.

verbosity() is a pure function (no model/serving), so the cost-per-correct column
is unit-testable. The "down vs baseline" bar needs a live served run → out of scope.
"""
import importlib.util
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_spec = importlib.util.spec_from_file_location(
    "eval_keystone", os.path.join(ROOT, "scripts", "eval_keystone.py"))
eval_keystone = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(eval_keystone)
verbosity = eval_keystone.verbosity


def test_counts_utf8_bytes():
    v = verbosity(["abc", "déf"], n_correct=2)   # 'déf' is 4 UTF-8 bytes (é = 2)
    assert v["total_reply_bytes"] == 3 + 4
    assert v["avg_reply_bytes"] == round((3 + 4) / 2, 1)


def test_bytes_per_correct_math():
    v = verbosity(["aaaa", "bb", "cccccc"], n_correct=2)   # 12 bytes total, 2 correct
    assert v["bytes_per_correct"] == 6.0
    assert v["words_per_correct"] == round(3 / 2, 1)        # 3 words / 2 correct


def test_guards_zero_correct():
    v = verbosity(["anything"], n_correct=0)
    assert v["bytes_per_correct"] is None
    assert v["words_per_correct"] is None
    assert v["total_reply_bytes"] == len("anything")


def test_guards_empty():
    v = verbosity([], n_correct=0)
    assert v["total_reply_bytes"] == 0
    assert v["avg_reply_bytes"] == 0.0
    assert v["bytes_per_correct"] is None


def test_summary_row_carries_bytes_per_correct():
    # the leaderboard summary must expose the Gate F field name
    assert "bytes_per_correct" in verbosity(["x"], 1)
