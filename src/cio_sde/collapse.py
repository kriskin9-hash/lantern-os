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
