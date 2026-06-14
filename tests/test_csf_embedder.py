"""Tests for csf_agent.embedder — issue #381."""
import tempfile
from pathlib import Path

import numpy as np
import pytest

from csf_agent.embedder import CSFEmbedder


@pytest.fixture
def emb():
    return CSFEmbedder()


def test_embed_known_tokens(emb):
    vec = emb.embed(["dream", "convergence"])
    assert isinstance(vec, np.ndarray)
    assert vec.dtype == np.float32
    assert vec.shape == (emb.vocab_size,)


def test_embed_unknown_tokens_zero(emb):
    """Unknown tokens must not raise and should produce a valid vector."""
    vec = emb.embed(["zzz_unknown_xyz", "foobar_99"])
    assert isinstance(vec, np.ndarray)
    assert vec.shape == (emb.vocab_size,)


def test_embed_empty_returns_zero_vector(emb):
    vec = emb.embed([])
    assert vec.shape == (emb.vocab_size,)
    assert np.allclose(vec, 0.0)


def test_embed_unit_norm(emb):
    vec = emb.embed(["dream", "agent", "loop"])
    norm = np.linalg.norm(vec)
    assert norm == pytest.approx(1.0, abs=1e-5)


def test_embed_mixed_known_unknown(emb):
    vec = emb.embed(["dream", "zzz_not_in_vocab"])
    assert vec.shape == (emb.vocab_size,)
    norm = np.linalg.norm(vec)
    assert norm == pytest.approx(1.0, abs=1e-5)


def test_save_load_roundtrip(emb):
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "embedder.npy"
        emb.save(path)
        emb2 = CSFEmbedder.load(path)
        v1 = emb.embed(["dream", "convergence"])
        v2 = emb2.embed(["dream", "convergence"])
        assert np.allclose(v1, v2, atol=1e-6)


def test_vocab_size_matches(emb):
    assert emb.vocab_size >= 34
    vec = emb.embed(["csf"])
    assert vec.shape[0] == emb.vocab_size
