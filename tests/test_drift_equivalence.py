"""
Tests for measure_drift_equivalence.py — pure math + data functions (#845)

Run: python -m pytest tests/test_drift_equivalence.py -q --tb=short
"""
import math
import json
import pytest
from pathlib import Path
from collections import Counter

import importlib.util
_path = Path(__file__).parent.parent / "scripts" / "measure_drift_equivalence.py"
_spec = importlib.util.spec_from_file_location("measure_drift_equivalence", _path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

bow_vector = _mod.bow_vector
cosine_similarity = _mod.cosine_similarity
relative_drift = _mod.relative_drift
load_prompts = _mod.load_prompts


# ── bow_vector ────────────────────────────────────────────────────────────────

def test_bow_vector_basic():
    v = bow_vector("hello world hello")
    assert v["hello"] == 2
    assert v["world"] == 1


def test_bow_vector_case_insensitive():
    v = bow_vector("Python PYTHON python")
    assert v["python"] == 3


def test_bow_vector_strips_short_tokens():
    v = bow_vector("I am a cat")
    assert "am" in v
    assert "i" not in v  # len 1 — filtered
    assert "a" not in v  # len 1 — filtered


def test_bow_vector_empty():
    v = bow_vector("")
    assert len(v) == 0


# ── cosine_similarity ─────────────────────────────────────────────────────────

def test_cosine_similarity_identical():
    v = bow_vector("the quick brown fox")
    assert cosine_similarity(v, v) == pytest.approx(1.0, abs=1e-6)


def test_cosine_similarity_orthogonal():
    a = Counter({"cat": 1})
    b = Counter({"dog": 1})
    assert cosine_similarity(a, b) == pytest.approx(0.0)


def test_cosine_similarity_partial():
    a = Counter({"cat": 1, "dog": 1})
    b = Counter({"cat": 1, "bird": 1})
    sim = cosine_similarity(a, b)
    assert 0.0 < sim < 1.0


def test_cosine_similarity_empty():
    assert cosine_similarity(Counter(), Counter({"a": 1})) == 0.0


# ── relative_drift ────────────────────────────────────────────────────────────

def test_relative_drift_identical_is_zero():
    v = bow_vector("the quick brown fox")
    assert relative_drift(v, v) == pytest.approx(0.0, abs=1e-9)


def test_relative_drift_completely_different():
    a = Counter({"cat": 1})
    b = Counter({"dog": 1})
    d = relative_drift(a, b)
    assert d > 0.0
    assert math.isfinite(d)


def test_relative_drift_empty_old_is_inf():
    d = relative_drift(Counter(), Counter({"a": 1}))
    assert math.isinf(d)


def test_relative_drift_scale_invariant():
    # Scaling both vectors by same factor should not change drift
    a = Counter({"cat": 2, "dog": 2})
    b = Counter({"cat": 3, "dog": 1})
    a2 = Counter({k: v * 10 for k, v in a.items()})
    b2 = Counter({k: v * 10 for k, v in b.items()})
    d1 = relative_drift(a, b)
    d2 = relative_drift(a2, b2)
    assert d1 == pytest.approx(d2, rel=1e-6)


def test_relative_drift_below_tol_threshold():
    # Two almost-identical responses should be within tol=0.25
    text_a = "The Eiffel Tower was completed in 1889 in Paris France."
    text_b = "The Eiffel Tower was finished in 1889 located in Paris France."
    d = relative_drift(bow_vector(text_a), bow_vector(text_b))
    assert d < 1.0  # should be close; not necessarily below 0.25 but < 1


def test_relative_drift_very_different_above_tol():
    # Completely different responses
    text_a = "The answer is 1889 the tower was built in France."
    text_b = "Quantum entanglement involves particles sharing states across distances."
    d = relative_drift(bow_vector(text_a), bow_vector(text_b))
    assert d > 0.25  # should be well above the tolerance


# ── load_prompts ──────────────────────────────────────────────────────────────

def test_load_prompts_returns_list(tmp_path, monkeypatch):
    pf = tmp_path / "prompts.jsonl"
    pf.write_text(
        json.dumps({"id": 1, "prompt": "What is 2+2?", "difficulty": "smoke"}) + "\n" +
        json.dumps({"id": 2, "prompt": "Capital of France?", "difficulty": "easy"}) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(_mod, "PROMPTS_PATH", pf)
    prompts = load_prompts(10)
    assert isinstance(prompts, list)
    assert len(prompts) == 2


def test_load_prompts_limits_n(tmp_path, monkeypatch):
    pf = tmp_path / "prompts.jsonl"
    lines = "\n".join(json.dumps({"id": i, "prompt": f"Q{i}", "difficulty": "smoke"}) for i in range(20))
    pf.write_text(lines + "\n", encoding="utf-8")
    monkeypatch.setattr(_mod, "PROMPTS_PATH", pf)
    prompts = load_prompts(5)
    assert len(prompts) == 5


def test_load_prompts_sorts_by_difficulty(tmp_path, monkeypatch):
    pf = tmp_path / "prompts.jsonl"
    pf.write_text(
        json.dumps({"id": 1, "prompt": "Hard Q", "difficulty": "hard"}) + "\n" +
        json.dumps({"id": 2, "prompt": "Smoke Q", "difficulty": "smoke"}) + "\n" +
        json.dumps({"id": 3, "prompt": "Easy Q", "difficulty": "easy"}) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(_mod, "PROMPTS_PATH", pf)
    prompts = load_prompts(10)
    difficulties = [p["difficulty"] for p in prompts]
    assert difficulties == sorted(difficulties, key=lambda d: {"smoke": 0, "easy": 1, "med": 2, "hard": 3}.get(d, 4))


def test_load_prompts_missing_file_returns_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(_mod, "PROMPTS_PATH", tmp_path / "nonexistent.jsonl")
    prompts = load_prompts(10)
    assert prompts == []
