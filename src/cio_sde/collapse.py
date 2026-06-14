"""
Σ₀ — Semantic Collapse Operator.

    Σ₀ : (x, Σ, G, u) → ⊥ₛ  or  x*

A first-class CIO operator that prevents divergence-by-wandering. When the
system is *underdetermined* — no optimization signal, a rank-deficient drift
Jacobian, an isotropically-flat dilation field, and control that cannot
distinguish actions — Σ₀ projects the state onto its minimal invariant
attractor manifold instead of letting it diverge, oscillate, or crash.

Embedded in the dynamics as:

    dx/dt = f(x,u,G) + w(t) − Σ₀(x,Σ,G,u)

Trigger (all four must hold — control singularity over a structureless field):

    1. ∇ₓ L → 0                       no further optimization signal
    2. rank(J_f) < threshold          drift Jacobian loses directional structure
    3. Σ isotropically flat            uncertainty has no preferred direction
    4. ∀u : Δcost(u) ≈ 0              control cannot distinguish actions

Outcomes:
    x*   degenerate fixed point — projection onto J's null eigenmodes
         (the "42 state": a stable, structureless summary)
    ⊥ₛ   semantic null — objective underdetermined, no latent geometry at all
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict

import torch

Tensor = torch.Tensor


class CollapseOutcome(str, Enum):
    NONE      = "none"        # not triggered
    ATTRACTOR = "attractor"   # x* — collapsed onto invariant manifold
    NULL      = "null"        # ⊥ₛ — semantic null state


@dataclass
class CollapseResult:
    triggered: bool
    outcome: CollapseOutcome
    x_star: Tensor
    metrics: Dict[str, float]

    def summary(self) -> str:
        m = self.metrics
        return (
            f"Σ₀[{self.outcome.value}] "
            f"∇L={m['grad_norm']:.4f} rank={m['eff_rank']:.1f}/{m['dim']:.0f} "
            f"aniso={m['anisotropy']:.4f} ∂H/∂u={m['ctrl_sens']:.4f}"
        )


class SemanticCollapseOperator:
    """Σ₀ — detects the underdetermined regime and collapses the state."""

    def __init__(self,
                 grad_eps: float = 1e-2,
                 rank_frac: float = 0.5,
                 anisotropy_eps: float = 5e-2,
                 ctrl_eps: float = 1e-2,
                 eig_eps: float = 1e-2) -> None:
        self.grad_eps = grad_eps          # ∇ₓL below this ⇒ no optimization signal
        self.rank_frac = rank_frac        # eff_rank/dim below this ⇒ rank-deficient
        self.anisotropy_eps = anisotropy_eps  # Σ eigval spread below this ⇒ flat
        self.ctrl_eps = ctrl_eps          # ∂H/∂u below this ⇒ control singularity
        self.eig_eps = eig_eps            # |λ| below this ⇒ null eigenmode

    @torch.no_grad()
    def _effective_rank(self, A: Tensor) -> float:
        # mean Jacobian over the batch; effective numerical rank via singular values
        Abar = A.mean(0)
        s = torch.linalg.svdvals(Abar)
        if s.numel() == 0 or s.max() <= 0:
            return 0.0
        return float((s > self.eig_eps * s.max()).sum().item())

    @torch.no_grad()
    def _anisotropy(self, sigma: Tensor) -> float:
        # spread of Σ eigenvalues, normalized — low ⇒ isotropic flatness
        sym = 0.5 * (sigma + sigma.transpose(-1, -2))
        ev = torch.linalg.eigvalsh(sym).clamp_min(1e-12)
        return float((ev.std(dim=-1) / ev.mean(dim=-1)).mean().item())

    def _grad_norm(self, model, x: Tensor, u: Tensor) -> float:
        xr = x.detach().clone().requires_grad_(True)
        L = model.stage_cost(xr, u.detach()).mean()
        (g,) = torch.autograd.grad(L, xr)
        return float(g.norm(dim=-1).mean().item())

    def _ctrl_sensitivity(self, model, x: Tensor, u: Tensor) -> float:
        ur = u.detach().clone().requires_grad_(True)
        H = model.stage_cost(x.detach(), ur).mean()
        (g,) = torch.autograd.grad(H, ur)
        return float(g.norm(dim=-1).mean().item())

    @torch.no_grad()
    def _collapse_state(self, x: Tensor, A: Tensor) -> tuple[Tensor, CollapseOutcome]:
        # project onto null eigenmodes of the (symmetrized) mean Jacobian
        Abar = 0.5 * (A.mean(0) + A.mean(0).T)
        evals, evecs = torch.linalg.eigh(Abar)
        null_mask = evals.abs() < self.eig_eps
        k = int(null_mask.sum().item())
        if k == 0:
            # no invariant directions at all → semantic null ⊥ₛ
            return torch.zeros_like(x), CollapseOutcome.NULL
        V = evecs[:, null_mask]                 # (d, k) null subspace basis
        P = V @ V.T                             # projector onto invariant manifold
        x_star = x @ P.T                        # degenerate fixed point
        return x_star, CollapseOutcome.ATTRACTOR

    def evaluate(self, model, x: Tensor, u: Tensor, sigma: Tensor,
                 A: Tensor) -> CollapseResult:
        dim = float(x.shape[-1])
        grad_norm = self._grad_norm(model, x, u)
        eff_rank = self._effective_rank(A)
        anisotropy = self._anisotropy(sigma)
        ctrl_sens = self._ctrl_sensitivity(model, x, u)

        cond_grad = grad_norm < self.grad_eps
        cond_rank = eff_rank < self.rank_frac * dim
        cond_flat = anisotropy < self.anisotropy_eps
        cond_ctrl = ctrl_sens < self.ctrl_eps
        triggered = cond_grad and cond_rank and cond_flat and cond_ctrl

        metrics = {
            "grad_norm": grad_norm, "eff_rank": eff_rank, "dim": dim,
            "anisotropy": anisotropy, "ctrl_sens": ctrl_sens,
        }
        if not triggered:
            return CollapseResult(False, CollapseOutcome.NONE, x, metrics)

        x_star, outcome = self._collapse_state(x, A)
        return CollapseResult(True, outcome, x_star, metrics)


# ── Lyapunov collapse-guarantee theorem ──────────────────────────────────────

@dataclass
class CollapseCertificate:
    """
    A computable certificate for the collapse-guarantee theorem.

    Theorem.  Let A be the drift Jacobian at a point and A_s = ½(A+Aᵀ) its
    symmetric part. Split the state space into the near-null subspace
    N = span{ vᵢ : |λᵢ(A_s)| < ε } and its complement M (the "active" modes).
    Take the Lyapunov function V(x) = ½‖P_M x‖² on the active subspace.

    If the spectral abscissa of A_s restricted to M is
            α = max{ λᵢ(A_s) : vᵢ ∈ M }  <  0,
    then  V̇ ≤ 2α V,  so  ‖P_M x(t)‖ ≤ ‖P_M x(0)‖ · e^{α t}:
    the active modes decay exponentially at rate |α| and the trajectory
    contracts onto the invariant null manifold N. Σ₀ collapse is GUARANTEED.

    If α ≥ 0 some active mode is non-contracting → collapse not guaranteed
    (the system may wander or diverge instead).
    """
    guaranteed: bool
    alpha: float            # spectral abscissa of active modes (V̇ ≤ 2α V)
    contraction_rate: float # |α| when guaranteed, else 0
    null_dim: int           # dimension of the invariant manifold
    active_dim: int

    def summary(self) -> str:
        verdict = "GUARANTEED" if self.guaranteed else "NOT guaranteed"
        return (
            f"collapse {verdict}: α={self.alpha:+.4f} "
            f"rate={self.contraction_rate:.4f} "
            f"null_dim={self.null_dim} active_dim={self.active_dim}"
        )


@torch.no_grad()
def collapse_certificate(A: Tensor, eig_eps: float = 1e-2,
                         margin: float = 0.0) -> CollapseCertificate:
    """Evaluate the collapse-guarantee theorem for a (batched) Jacobian A."""
    Abar = A.mean(0) if A.dim() == 3 else A
    A_s = 0.5 * (Abar + Abar.T)
    evals = torch.linalg.eigvalsh(A_s)
    null_mask = evals.abs() < eig_eps
    active = evals[~null_mask]
    null_dim = int(null_mask.sum().item())
    if active.numel() == 0:
        # entirely null — already on the manifold, trivially collapsed
        return CollapseCertificate(True, float("-inf"), float("inf"),
                                   null_dim, 0)
    alpha = float(active.max().item())
    guaranteed = alpha < -margin
    return CollapseCertificate(
        guaranteed=guaranteed,
        alpha=alpha,
        contraction_rate=(-alpha if guaranteed else 0.0),
        null_dim=null_dim,
        active_dim=int(active.numel()),
    )


@torch.no_grad()
def lyapunov_value(x: Tensor, A: Tensor, eig_eps: float = 1e-2) -> float:
    """V(x) = ½‖P_M x‖² — energy in the active (non-null) subspace of A_s."""
    Abar = A.mean(0) if A.dim() == 3 else A
    A_s = 0.5 * (Abar + Abar.T)
    evals, evecs = torch.linalg.eigh(A_s)
    active = evecs[:, evals.abs() >= eig_eps]      # (d, m)
    if active.shape[1] == 0:
        return 0.0
    xm = x @ active                                # project onto active modes
    return float(0.5 * (xm ** 2).sum(-1).mean().item())


# ── Σ₀⁻¹ Anti-Collapse Operator ──────────────────────────────────────────────

class AntiCollapseOperator:
    """
    Σ₀⁻¹ — prevents 42-states by persistent excitation along null modes.

    Where Σ₀ projects ONTO the null subspace (collapse), Σ₀⁻¹ injects energy
    ALONG it. As the system approaches the collapse boundary it loses
    directional structure; Σ₀⁻¹ restores rank and re-anisotropizes Σ by adding a
    perturbation in exactly the directions that have gone flat — the
    persistent-excitation principle from adaptive control.

        dx = f dt + dW + Σ₀⁻¹,   Σ₀⁻¹ = strength · p · (V_null · ξ)

    `p ∈ [0,1]` is collapse proximity: 0 when far from the boundary (no-op),
    rising to 1 as ∇L, Jacobian rank, Σ anisotropy and control sensitivity all
    approach their collapse thresholds. The excitation is gated by p so it costs
    nothing in healthy regimes and only fires near a 42-state.
    """

    def __init__(self, detector: Optional[SemanticCollapseOperator] = None,
                 strength: float = 0.5, eig_eps: float = 1e-2) -> None:
        self.detector = detector or SemanticCollapseOperator()
        self.strength = strength
        self.eig_eps = eig_eps

    def proximity(self, model, x: Tensor, u: Tensor, sigma: Tensor,
                  A: Tensor) -> float:
        """How close the state is to a collapse (0 = safe, 1 = collapsing)."""
        d = self.detector
        grad_norm = d._grad_norm(model, x, u)
        eff_rank = d._effective_rank(A)
        aniso = d._anisotropy(sigma)
        ctrl = d._ctrl_sensitivity(model, x, u)
        dim = float(x.shape[-1])
        # each term → 1 as it sinks below its trigger threshold
        p_grad = _below(grad_norm, d.grad_eps)
        p_rank = _below(eff_rank, d.rank_frac * dim)
        p_flat = _below(aniso, d.anisotropy_eps)
        p_ctrl = _below(ctrl, d.ctrl_eps)
        return min(p_grad, p_rank, p_flat, p_ctrl)   # all must be near to act

    @torch.no_grad()
    def excite(self, x: Tensor, sigma: Tensor, A: Tensor, p: float,
               noise: Tensor) -> tuple[Tensor, Tensor]:
        """Return (dx_extra, sigma_extra) injected along the null subspace."""
        Abar = 0.5 * (A.mean(0) + A.mean(0).T)
        evals, evecs = torch.linalg.eigh(Abar)
        null = evecs[:, evals.abs() < self.eig_eps]      # (d, k)
        if null.shape[1] == 0:
            return torch.zeros_like(x), torch.zeros_like(sigma)
        coeff = noise @ null                              # (B, k) random in null
        dx_extra = self.strength * p * (coeff @ null.T)   # back to state space
        # re-anisotropize Σ along the recovered directions
        bump = self.strength * p * (null @ null.T)
        sigma_extra = bump.unsqueeze(0).expand_as(sigma)
        return dx_extra, sigma_extra


def _below(value: float, threshold: float) -> float:
    """Soft indicator → 1 when value ≪ threshold, 0 when value ≥ threshold."""
    if threshold <= 0:
        return 0.0
    return max(0.0, min(1.0, 1.0 - value / threshold))
