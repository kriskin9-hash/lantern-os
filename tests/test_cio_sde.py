"""Tests for the CIO Neural SDE engine — issue #392."""
import pytest

torch = pytest.importorskip("torch")

from src.cio_sde import (
    CIO_SDE, Dynamics, rollout, analyze_trajectory, free_energy, gaussian_kl,
    SemanticCollapseOperator, CollapseOutcome,
)


def _model(dim=4, ctrl=2, hidden=16, seed=0):
    torch.manual_seed(seed)
    return CIO_SDE(dim=dim, ctrl_dim=ctrl, hidden=hidden)


def _init_state(b=8, dim=4, scale=1.0):
    x0 = scale * torch.randn(b, dim)
    s0 = torch.eye(dim).expand(b, dim, dim).clone()
    return x0, s0


# ── SDE rollout ──────────────────────────────────────────────────────────────

def test_rollout_shapes():
    m = _model()
    x0, s0 = _init_state()
    xf, sf, tr = rollout(m, x0, s0, steps=10)
    assert xf.shape == x0.shape
    assert sf.shape == s0.shape
    assert len(tr.steps) == 10


def test_sde_bounded_under_noise():
    """Success criterion: SDE does not explode under bounded noise."""
    m = _model()
    x0, s0 = _init_state()
    _, _, tr = rollout(m, x0, s0, steps=80, dt=0.05)
    rep = analyze_trajectory(tr)
    assert not rep.diverged
    assert all(v == v for v in tr.x_norms())  # no NaN


def test_covariance_stays_psd_and_bounded():
    """Kalman-Bucy Riccati keeps Σ symmetric, PSD, and bounded."""
    m = _model()
    x0, s0 = _init_state()
    _, sf, tr = rollout(m, x0, s0, steps=60)
    sym = 0.5 * (sf + sf.transpose(-1, -2))
    assert torch.allclose(sf, sym, atol=1e-4)              # symmetric
    ev = torch.linalg.eigvalsh(sym)
    assert (ev > -1e-3).all()                              # PSD
    assert analyze_trajectory(tr).sigma_bounded


# ── Replay (invariant 2) ─────────────────────────────────────────────────────

def test_rollout_is_replayable():
    m = _model()
    x0, s0 = _init_state()
    xf1, sf1, _ = rollout(m, x0, s0, steps=40, base_seed=123)
    xf2, sf2, _ = rollout(m, x0, s0, steps=40, base_seed=123)
    assert torch.allclose(xf1, xf2, atol=1e-6)
    assert torch.allclose(sf1, sf2, atol=1e-6)


def test_different_seed_different_trajectory():
    m = _model()
    x0, s0 = _init_state()
    xf1, _, _ = rollout(m, x0, s0, steps=40, base_seed=1)
    xf2, _, _ = rollout(m, x0, s0, steps=40, base_seed=2)
    assert not torch.allclose(xf1, xf2, atol=1e-4)


# ── Free energy ──────────────────────────────────────────────────────────────

def test_gaussian_kl_zero_for_identical():
    mu = torch.zeros(4, 4)
    sig = torch.eye(4).expand(4, 4, 4).clone()
    kl = gaussian_kl(mu, sig, mu, sig)
    assert torch.allclose(kl, torch.zeros(4), atol=1e-5)


def test_gaussian_kl_nonnegative():
    mu_q = torch.randn(4, 4)
    sig_q = torch.eye(4).expand(4, 4, 4).clone() * 0.5
    mu_p = torch.zeros(4, 4)
    sig_p = torch.eye(4).expand(4, 4, 4).clone()
    assert (gaussian_kl(mu_q, sig_q, mu_p, sig_p) >= -1e-5).all()


def test_free_energy_finite_and_differentiable():
    m = _model()
    x0, s0 = _init_state()
    u = m.pcsf(x0, s0)
    F = free_energy(m, x0, u, s0).mean()
    assert torch.isfinite(F)
    F.backward()
    grads = [p.grad for p in m.parameters() if p.grad is not None]
    assert len(grads) > 0


# ── PCSF control ─────────────────────────────────────────────────────────────

def test_pcsf_respects_hard_clamp():
    """Invariant 1: control can never exceed the NAP hard bound."""
    m = CIO_SDE(dim=4, ctrl_dim=2, hidden=16)
    m.pcsf.u_max = 1.0
    x = 100.0 * torch.randn(8, 4)
    s = torch.eye(4).expand(8, 4, 4).clone()
    u = m.pcsf(x, s)
    assert u.abs().max() <= 1.0 + 1e-5


# ── Hot-swap (invariant 3) ───────────────────────────────────────────────────

def test_hot_swap_accepts_equivalent_node():
    m = _model()
    x0, s0 = _init_state()
    twin = Dynamics(4, 2, 16)
    twin.load_state_dict(m.graph.active.state_dict())   # behaviourally identical
    u = m.pcsf(x0, s0)
    rec = m.graph.hot_swap(twin, x0, u, step=0)
    assert rec.accepted
    assert rec.drift_delta < 1e-5
    assert m.graph.active is twin


def test_hot_swap_rejects_divergent_node():
    m = _model()
    x0, s0 = _init_state()
    torch.manual_seed(999)
    stranger = Dynamics(4, 2, 16)                        # unrelated weights
    u = m.pcsf(x0, s0)
    original = m.graph.active
    rec = m.graph.hot_swap(stranger, x0, u, step=0)
    assert not rec.accepted
    assert m.graph.active is original                    # unchanged on reject


# ── Σ₀ Semantic Collapse Operator ────────────────────────────────────────────

def test_collapse_dormant_in_structured_regime():
    m = _model()
    m.collapse_op = SemanticCollapseOperator()
    x0, s0 = _init_state(scale=1.0)
    _, _, tr = rollout(m, x0, s0, steps=40, base_seed=1)
    assert len(tr.collapses) == 0


def test_collapse_fires_in_degenerate_regime():
    """Zero drift Jacobian + near-origin + isotropic Σ ⇒ Σ₀ triggers."""
    m = _model()
    for p in m.graph.active.drift_net.parameters():
        torch.nn.init.zeros_(p)
    m.collapse_op = SemanticCollapseOperator()
    x0, s0 = _init_state(scale=0.01)
    _, _, tr = rollout(m, x0, s0, steps=20, base_seed=1)
    assert len(tr.collapses) > 0
    assert tr.collapses[0]["result"].outcome in (
        CollapseOutcome.ATTRACTOR, CollapseOutcome.NULL)


def test_collapse_freezes_state():
    """When Σ₀ fires, dx→0: the collapsed state stops moving."""
    m = _model()
    for p in m.graph.active.drift_net.parameters():
        torch.nn.init.zeros_(p)
    m.collapse_op = SemanticCollapseOperator()
    x0, s0 = _init_state(scale=0.01)
    xf, _, tr = rollout(m, x0, s0, steps=20, base_seed=1)
    # last few x-norms should be essentially constant (frozen attractor)
    norms = tr.x_norms()
    assert abs(norms[-1] - norms[-2]) < 1e-3
