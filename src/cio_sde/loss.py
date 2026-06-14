"""
Variational free energy — the training objective that defines "convergence".

Minimizing free energy F is exactly CIO invariant 5: the system converges only
in stable dilation regions. F → minimum ⇔ x reaches the goal AND Σ collapses to
the prior (KL → 0), i.e. the dilation field settles into a low, stable regime.

    F = goal_cost(x)  +  control_cost(u)  +  KL[ q(x,Σ) ‖ p(x,Σ_prior) ]

PCSF made principled: u* is the control that minimizes expected free energy,
not an ad-hoc weighted cost.
"""

from __future__ import annotations

import torch

Tensor = torch.Tensor


def gaussian_kl(mu_q: Tensor, sigma_q: Tensor,
                mu_p: Tensor, sigma_p: Tensor) -> Tensor:
    """
    KL[ N(mu_q, Σ_q) ‖ N(mu_p, Σ_p) ] for batched full covariances.

    KL = ½[ tr(Σp⁻¹ Σq) + (μp−μq)ᵀ Σp⁻¹ (μp−μq) − d + ln(det Σp / det Σq) ]
    """
    d = mu_q.shape[-1]
    Lp = torch.linalg.cholesky(sigma_p)
    # Σp⁻¹ Σq  via solving Σp X = Σq
    sp_inv_sq = torch.cholesky_solve(sigma_q, Lp)
    tr_term = torch.diagonal(sp_inv_sq, dim1=-2, dim2=-1).sum(-1)

    dmu = (mu_p - mu_q).unsqueeze(-1)
    sp_inv_dmu = torch.cholesky_solve(dmu, Lp)
    quad = (dmu.transpose(-1, -2) @ sp_inv_dmu).squeeze(-1).squeeze(-1)

    logdet_p = 2.0 * torch.log(torch.diagonal(Lp, dim1=-2, dim2=-1)).sum(-1)
    Lq = torch.linalg.cholesky(sigma_q)
    logdet_q = 2.0 * torch.log(torch.diagonal(Lq, dim1=-2, dim2=-1)).sum(-1)

    return 0.5 * (tr_term + quad - d + logdet_p - logdet_q)


def free_energy(model, x: Tensor, u: Tensor, sigma: Tensor,
                sigma_prior_scale: float = 1.0) -> Tensor:
    """
    Variational free energy at a state. Lower = more converged.

    goal/control costs come from the model's stage cost; the KL pulls the belief
    (x, Σ) toward the goal prior N(x*, sI), so collapsing Σ is rewarded.
    """
    goal_ctrl = model.stage_cost(x, u)
    d = x.shape[-1]
    sigma_prior = (sigma_prior_scale * torch.eye(d, device=x.device)
                   ).expand(x.shape[0], d, d)
    mu_p = model.x_target.expand_as(x)
    kl = gaussian_kl(x, sigma, mu_p, sigma_prior)
    return goal_ctrl + kl
