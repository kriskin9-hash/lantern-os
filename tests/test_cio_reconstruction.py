"""Tests for the Σ₀ᴿ reconstruction operator — the "put the smoke back" machine.

These pin the honest guarantees the whitepaper leans on (prediction P5 and the
"universe on a flash drive" thesis):

  • collapse genuinely burns the active modes (the "smoke" is gone),
  • a full-record seed reconstructs near-losslessly,
  • bigger seed → never-worse distortion (a real rate–distortion curve),
  • there is a hard FLOOR: a partial seed cannot beat the record it kept,
  • reference reconstruction beats random re-excitation (record > no record).

Deterministic: fixed seed, no network. Run:
    python -m pytest tests/test_cio_reconstruction.py -q
"""
from __future__ import annotations

import pytest

torch = pytest.importorskip("torch")

from cio_sde import (
    ReconstructionOperator,
    collapse_certificate,
    lyapunov_value,
)

SEED = 7
DIM = 16
NULL_DIM = 6
BATCH = 128
EPS = 1e-2
ACTIVE_DIM = DIM - NULL_DIM


def _orthonormal(n: int, g: torch.Generator) -> torch.Tensor:
    q, _ = torch.linalg.qr(torch.randn(n, n, generator=g))
    return q


def _build_world(g: torch.Generator):
    """A guaranteed-contracting symmetric A and a compressible state x0.

    x0's structure has a steep dominant head plus a faint tail — so a small seed
    captures most of it, but perfect reconstruction needs the whole record.
    """
    Q = _orthonormal(DIM, g)
    eig = torch.zeros(DIM)
    eig[NULL_DIM:] = -torch.linspace(0.3, 1.5, ACTIVE_DIM)   # active modes contract
    A = (Q * eig) @ Q.T
    c = torch.zeros(BATCH, DIM)
    c[:, :NULL_DIM] = torch.randn(BATCH, NULL_DIM, generator=g)
    decay = 0.30 ** torch.arange(ACTIVE_DIM).float()
    c[:, NULL_DIM:] = decay * 4.0 + 0.05 * torch.randn(BATCH, ACTIVE_DIM, generator=g)
    return A, c @ Q.T


@pytest.fixture(scope="module")
def world():
    g = torch.Generator().manual_seed(SEED)
    A, x0 = _build_world(g)
    return A, x0


@pytest.fixture(scope="module")
def op():
    return ReconstructionOperator(eig_eps=EPS)


def _distortion(x_hat, x0):
    return float((x_hat - x0).norm(dim=-1).mean())


def test_certificate_guarantees_collapse(world):
    A, _ = world
    cert = collapse_certificate(A.unsqueeze(0), eig_eps=EPS)
    assert cert.guaranteed, cert.summary()
    assert cert.null_dim == NULL_DIM
    assert cert.active_dim == ACTIVE_DIM


def test_collapse_burns_active_energy(world, op):
    """After the burn, the active-mode (structure) energy is ~0; null survives."""
    A, x0 = world
    pre = lyapunov_value(x0, A.unsqueeze(0), eig_eps=EPS)
    x_burnt = op.collapse(x0, A)
    post = lyapunov_value(x_burnt, A.unsqueeze(0), eig_eps=EPS)
    assert pre > 1e-3
    assert post < 1e-6           # the smoke is gone
    # the null-manifold component is preserved by the burn
    V = op._active_basis(A)
    null_pre = x0 - (x0 @ V) @ V.T
    assert torch.allclose(x_burnt, null_pre, atol=1e-5)


def test_zero_seed_is_the_burnt_state(world, op):
    A, x0 = world
    x_burnt = op.collapse(x0, A)
    rebuilt = op.reconstruct(x_burnt, op.seed(x0, A, 0))
    assert torch.allclose(rebuilt, x_burnt, atol=1e-6)


def test_full_seed_is_near_lossless(world, op):
    """Keeping the whole record reconstructs the original to within tolerance."""
    A, x0 = world
    x_burnt = op.collapse(x0, A)
    rebuilt = op.reconstruct(x_burnt, op.seed(x0, A, ACTIVE_DIM))
    assert _distortion(rebuilt, x0) < 1e-4


def test_rate_distortion_is_monotone_nonincreasing(world, op):
    """Bigger speck → never-worse reconstruction (a real R–D curve)."""
    A, x0 = world
    x_burnt = op.collapse(x0, A)
    dists = [
        _distortion(op.reconstruct(x_burnt, op.seed(x0, A, k)), x0)
        for k in range(ACTIVE_DIM + 1)
    ]
    for earlier, later in zip(dists, dists[1:]):
        assert later <= earlier + 1e-6
    assert dists[0] > dists[-1]   # curve actually descends


def test_partial_seed_has_a_floor_but_beats_burnt(world, op):
    """A partial record can't be lossless (floor > 0) yet still beats the burn."""
    A, x0 = world
    x_burnt = op.collapse(x0, A)
    burnt_d = _distortion(x_burnt, x0)
    k = ACTIVE_DIM // 2
    partial_d = _distortion(op.reconstruct(x_burnt, op.seed(x0, A, k)), x0)
    assert partial_d > 1e-4          # floor: cannot rebuild what was not kept
    assert partial_d < burnt_d       # but strictly better than doing nothing


def test_reference_beats_random_reexcitation(world, op):
    """The record (reference) reconstructs better than random energy of equal size."""
    A, x0 = world
    x_burnt = op.collapse(x0, A)
    rng = torch.Generator().manual_seed(SEED + 1)
    V = op._active_basis(A)
    for k in (1, ACTIVE_DIM // 2, ACTIVE_DIM):
        s = op.seed(x0, A, k)
        ref_d = _distortion(op.reconstruct(x_burnt, s), x0)
        energy = (s["coeffs"] ** 2).sum(-1).sqrt().unsqueeze(-1)
        rnd = torch.randn(BATCH, V.shape[1], generator=rng) @ V.T
        rnd = rnd / (rnd.norm(dim=-1, keepdim=True) + 1e-12) * energy
        rand_d = _distortion(x_burnt + rnd, x0)
        assert ref_d <= rand_d + 1e-6, f"k={k}: ref {ref_d} should beat random {rand_d}"
