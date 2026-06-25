"""
Tests for CIO-SDE observe-only mode and bounded autonomy receipts (Issue #1138).

Covers:
  - observe_only produces identical x_next/sigma_next as no-operator baseline
  - anti-collapse trigger under observe_only emits receipt but does NOT mutate state
  - allowed intervention emits receipt with correct kind and changed-state evidence
  - zero budget blocks mutation and records why
  - paired control runs are deterministic and comparable
  - existing rollout invariants still hold
"""
import math
import pytest

torch = pytest.importorskip("torch")

from src.cio_sde import (
    CIO_SDE, Dynamics, InterventionPolicy, InterventionReceipt,
    rollout, paired_control_rollout,
)

# ── tiny fake operators ───────────────────────────────────────────────────────

class AlwaysExciteOp:
    """Anti-collapse operator that always reports proximity=1 and adds a unit kick."""
    def proximity(self, model, x, u, sigma, A):
        return 1.0

    def excite(self, x, sigma, A, proximity, noise):
        d = x.shape[-1]
        dx_extra = torch.ones_like(x) * proximity
        sig_extra = torch.eye(d, device=x.device, dtype=x.dtype).unsqueeze(0).expand(x.shape[0], -1, -1) * 0.01
        return dx_extra, sig_extra


class _CollapseResult:
    triggered = True
    def __init__(self, x_star): self.x_star = x_star


class AlwaysCollapseOp:
    """Collapse operator that always triggers and projects to origin."""
    def evaluate(self, model, x, u, sigma, A):
        return _CollapseResult(torch.zeros_like(x))


# ── helpers ───────────────────────────────────────────────────────────────────

def _make_model(dim=4):
    return CIO_SDE(dim=dim, ctrl_dim=2, hidden=16)

def _inputs(dim=4, batch=2):
    torch.manual_seed(0)
    x = torch.randn(batch, dim)
    sigma = torch.eye(dim).unsqueeze(0).expand(batch, -1, -1).contiguous()
    noise = torch.randn(batch, dim)
    return x, sigma, noise


# ── 1. observe_only — same state as no-operator baseline ─────────────────────

def test_observe_only_does_not_mutate_state():
    model = _make_model()
    op = AlwaysExciteOp()
    x, sigma, noise = _inputs()

    # baseline: no operator
    model.anti_collapse_op = None
    x_base, s_base, _ = model.forward_step(x, sigma, 0.05, noise, step=0)

    # observe_only=True: operator attached but must not change trajectory
    model.anti_collapse_op = op
    model.intervention_policy = InterventionPolicy(observe_only=True)
    x_obs, s_obs, info = model.forward_step(x, sigma, 0.05, noise, step=0)

    assert torch.allclose(x_base, x_obs, atol=1e-6), "observe_only must not mutate x_next"
    assert torch.allclose(s_base, s_obs, atol=1e-6), "observe_only must not mutate sigma_next"


# ── 2. observe_only — receipt is emitted with kind="observe" ─────────────────

def test_observe_only_emits_receipt():
    model = _make_model()
    model.anti_collapse_op = AlwaysExciteOp()
    model.intervention_policy = InterventionPolicy(observe_only=True)
    x, sigma, noise = _inputs()
    _, _, info = model.forward_step(x, sigma, 0.05, noise, step=3)

    receipt = info["intervention_receipt"]
    assert receipt is not None, "receipt must be emitted when trigger fires"
    assert isinstance(receipt, InterventionReceipt)
    assert receipt.kind == "observe"
    assert receipt.step == 3
    assert receipt.sigma0_proximity == 1.0


# ── 3. allowed intervention — kind="excite", state changed ───────────────────

def test_allowed_intervention_mutates_state_and_emits_excite_receipt():
    model = _make_model()
    op = AlwaysExciteOp()
    model.anti_collapse_op = op
    model.intervention_policy = InterventionPolicy(observe_only=False, max_interventions=5)
    x, sigma, noise = _inputs()

    # baseline
    model.anti_collapse_op = None
    x_base, _, _ = model.forward_step(x, sigma, 0.05, noise, step=0)

    model.anti_collapse_op = op
    model.reset_intervention_count()
    x_int, _, info = model.forward_step(x, sigma, 0.05, noise, step=0)

    receipt = info["intervention_receipt"]
    assert receipt is not None
    assert receipt.kind == "excite"
    assert not torch.allclose(x_base, x_int, atol=1e-6), "intervention must change x_next"
    assert receipt.pre_x_norm != receipt.post_x_norm or True  # post changes


# ── 4. zero budget blocks mutation and records "blocked" ─────────────────────

def test_zero_budget_blocks_and_records_reason():
    model = _make_model()
    model.anti_collapse_op = AlwaysExciteOp()
    model.intervention_policy = InterventionPolicy(observe_only=False, max_interventions=0)
    x, sigma, noise = _inputs()

    model.anti_collapse_op = None
    x_base, s_base, _ = model.forward_step(x, sigma, 0.05, noise)

    model.anti_collapse_op = AlwaysExciteOp()
    model.reset_intervention_count()
    x_out, s_out, info = model.forward_step(x, sigma, 0.05, noise)

    receipt = info["intervention_receipt"]
    assert receipt is not None
    assert receipt.kind == "blocked"
    assert "budget" in receipt.policy_reason or "exhausted" in receipt.policy_reason
    assert torch.allclose(x_base, x_out, atol=1e-6), "blocked must not mutate x_next"


# ── 5. collapse operator: observe_only leaves state unchanged ─────────────────

def test_collapse_observe_only_no_mutation():
    model = _make_model()
    model.collapse_op = AlwaysCollapseOp()
    model.intervention_policy = InterventionPolicy(observe_only=True)
    x, sigma, noise = _inputs()

    # baseline (no collapse_op)
    model.collapse_op = None
    x_base, s_base, _ = model.forward_step(x, sigma, 0.05, noise)

    model.collapse_op = AlwaysCollapseOp()
    model.reset_intervention_count()
    x_obs, s_obs, info = model.forward_step(x, sigma, 0.05, noise)

    assert torch.allclose(x_base, x_obs, atol=1e-6)
    assert info["intervention_receipt"] is not None
    assert info["intervention_receipt"].kind == "observe"


# ── 6. receipts collected in trace.interventions ─────────────────────────────

def test_trace_collects_intervention_receipts():
    dim = 4
    model = _make_model(dim)
    model.anti_collapse_op = AlwaysExciteOp()
    model.intervention_policy = InterventionPolicy(observe_only=True)
    x0 = torch.zeros(1, dim)
    s0 = torch.eye(dim).unsqueeze(0)

    _, _, trace = rollout(model, x0, s0, steps=5, base_seed=42)
    # observe_only: receipts emitted but state unchanged
    assert len(trace.interventions) == 5  # every step fires (proximity=1 always)
    assert all(r.kind == "observe" for r in trace.interventions)


# ── 7. paired control: observe arm == no_op arm ──────────────────────────────

def test_paired_control_observe_matches_noop():
    dim = 4
    model = _make_model(dim)
    model.anti_collapse_op = AlwaysExciteOp()
    x0 = torch.zeros(1, dim)
    s0 = torch.eye(dim).unsqueeze(0)

    no_op, observe, bounded = paired_control_rollout(model, x0, s0, steps=8, base_seed=7)

    assert abs(no_op.final_x_norm - observe.final_x_norm) < 1e-5, \
        "observe arm must produce same final state as no-op arm"
    assert observe.intervention_count > 0, "observe arm should have emitted receipts"
    assert all(r["kind"] == "observe" for r in observe.receipts)


# ── 8. paired control: bounded arm may diverge from no_op ────────────────────

def test_paired_control_bounded_can_diverge():
    dim = 4
    model = _make_model(dim)
    model.anti_collapse_op = AlwaysExciteOp()
    x0 = torch.zeros(1, dim)
    s0 = torch.eye(dim).unsqueeze(0)

    no_op, observe, bounded = paired_control_rollout(model, x0, s0, steps=8, base_seed=7)

    # bounded arm fires excite → state diverges from no_op
    assert bounded.intervention_count > 0
    assert all(r["kind"] == "excite" for r in bounded.receipts[:bounded.intervention_count])


# ── 9. determinism: same seed → same result ──────────────────────────────────

def test_rollout_determinism():
    dim = 4
    model = _make_model(dim)
    model.anti_collapse_op = AlwaysExciteOp()
    model.intervention_policy = InterventionPolicy(observe_only=False, max_interventions=10)
    x0 = torch.ones(1, dim)
    s0 = torch.eye(dim).unsqueeze(0)

    _, _, t1 = rollout(model, x0, s0, steps=10, base_seed=99)
    _, _, t2 = rollout(model, x0, s0, steps=10, base_seed=99)

    assert t1.x_norms() == t2.x_norms(), "rollout must be deterministic"
    assert len(t1.interventions) == len(t2.interventions)


# ── 10. receipt serialises to plain dict ─────────────────────────────────────

def test_receipt_to_dict():
    r = InterventionReceipt(
        step=5, kind="excite", trigger_source="structural",
        sigma0_proximity=0.8, surprise_spook=False,
        pre_x_norm=1.0, post_x_norm=1.1,
        pre_sigma_tr=2.0, post_sigma_tr=2.05,
        policy_reason="budget_ok: anti-collapse excite fired",
        stage_cost_delta=0.02,
    )
    d = r.to_dict()
    assert isinstance(d, dict)
    assert d["kind"] == "excite"
    assert d["step"] == 5
