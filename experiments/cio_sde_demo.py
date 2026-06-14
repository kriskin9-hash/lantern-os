"""
CIO Neural SDE — runnable demonstration (#392).

Exercises the four CIO success criteria as separate scenarios:

  1. STABILITY   — SDE stays bounded under noise; Σ stabilizes via Riccati
  2. REPLAY      — same seed reproduces the trajectory bit-for-bit
  3. HOT-SWAP    — equivalent node accepted, divergent node rejected
  4. Σ₀ COLLAPSE — underdetermined regime collapses to invariant attractor

Run:
    python experiments/cio_sde_demo.py
    PYTHONIOENCODING=utf-8 python experiments/cio_sde_demo.py   # Windows console
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import torch

from src.cio_sde import (
    CIO_SDE, Dynamics, LinearDynamics, rollout, analyze_trajectory, free_energy,
    SemanticCollapseOperator, AntiCollapseOperator,
    collapse_certificate, lyapunov_value,
)


def banner(title: str) -> None:
    print("\n" + "=" * 64)
    print(f"  {title}")
    print("=" * 64)


def scenario_stability() -> None:
    banner("1. STABILITY — bounded SDE + Riccati covariance")
    torch.manual_seed(0)
    m = CIO_SDE(dim=6, ctrl_dim=3, hidden=48)
    x0 = torch.randn(16, 6)
    s0 = torch.eye(6).expand(16, 6, 6).clone()
    _, _, tr = rollout(m, x0, s0, steps=120, dt=0.05, base_seed=7)
    rep = analyze_trajectory(tr)
    print(rep.summary())
    print(f"  Σ trace: start {tr.sigma_traces()[0]:.3f} → end {tr.sigma_traces()[-1]:.3f} "
          f"(Riccati equilibrium, bounded={rep.sigma_bounded})")


def scenario_replay() -> None:
    banner("2. REPLAY — trajectory reconstructable from trace seed")
    torch.manual_seed(1)
    m = CIO_SDE(dim=4, ctrl_dim=2, hidden=32)
    x0 = torch.randn(8, 4)
    s0 = torch.eye(4).expand(8, 4, 4).clone()
    xa, _, _ = rollout(m, x0, s0, steps=50, base_seed=42)
    xb, _, _ = rollout(m, x0, s0, steps=50, base_seed=42)
    xc, _, _ = rollout(m, x0, s0, steps=50, base_seed=43)
    print(f"  seed 42 == seed 42 : {torch.allclose(xa, xb, atol=1e-6)}  (replayable)")
    print(f"  seed 42 == seed 43 : {torch.allclose(xa, xc, atol=1e-4)}  (noise-distinct)")


def scenario_hot_swap() -> None:
    banner("3. HOT-SWAP — σ: v₁→v₂ with behavioural-equivalence guard")
    torch.manual_seed(2)
    m = CIO_SDE(dim=4, ctrl_dim=2, hidden=32)
    x0 = torch.randn(8, 4)
    s0 = torch.eye(4).expand(8, 4, 4).clone()
    u = m.pcsf(x0, s0)

    twin = Dynamics(4, 2, 32)
    twin.load_state_dict(m.graph.active.state_dict())
    rec_ok = m.graph.hot_swap(twin, x0, u, step=10)
    print(f"  equivalent node : accepted={rec_ok.accepted}  Δ={rec_ok.drift_delta:.2e}")

    torch.manual_seed(777)
    stranger = Dynamics(4, 2, 32)
    rec_no = m.graph.hot_swap(stranger, x0, u, step=20)
    print(f"  divergent node  : accepted={rec_no.accepted}  Δ={rec_no.drift_delta:.3f}  "
          f"({rec_no.reason})")


def scenario_collapse() -> None:
    banner("4. Σ₀ COLLAPSE — underdetermined regime → invariant attractor")
    torch.manual_seed(3)

    # structured system: Σ₀ attached but stays dormant
    m = CIO_SDE(dim=4, ctrl_dim=2, hidden=32)
    m.collapse_op = SemanticCollapseOperator()
    x0 = torch.randn(8, 4)
    s0 = torch.eye(4).expand(8, 4, 4).clone()
    _, _, tr = rollout(m, x0, s0, steps=40, base_seed=1)
    print(f"  structured regime : Σ₀ fired {len(tr.collapses)}/40 steps (dormant)")

    # degenerate system: zero drift Jacobian, near origin, isotropic Σ
    m2 = CIO_SDE(dim=4, ctrl_dim=2, hidden=32)
    for p in m2.graph.active.drift_net.parameters():
        torch.nn.init.zeros_(p)
    m2.collapse_op = SemanticCollapseOperator()
    x0b = 0.01 * torch.randn(8, 4)
    s0b = torch.eye(4).expand(8, 4, 4).clone()
    xf, _, tr2 = rollout(m2, x0b, s0b, steps=40, base_seed=1)
    print(f"  degenerate regime : Σ₀ fired {len(tr2.collapses)}/40 steps")
    if tr2.collapses:
        print(f"    {tr2.collapses[0]['result'].summary()}")
    norms = tr2.x_norms()
    print(f"    state frozen onto attractor: ‖x‖ {norms[0]:.4f} → {norms[-1]:.4f}")


def scenario_certificate() -> None:
    banner("6. LYAPUNOV CERTIFICATE — guaranteed collapse + verified contraction")
    # stable linear node: drift Jacobian is exactly A = -0.8 I
    A = -0.8 * torch.eye(5)
    cert = collapse_certificate(A.unsqueeze(0))
    print(f"  A = -0.8·I : {cert.summary()}")
    node = LinearDynamics(A, B=torch.zeros(5, 2))
    m = CIO_SDE(dim=5, ctrl_dim=2, hidden=8)
    m.graph.active = node
    m.pcsf.u_max = 1e-6
    x0 = torch.randn(64, 5)
    s0 = torch.eye(5).expand(64, 5, 5).clone()
    xf, _, tr = rollout(m, x0, s0, steps=120, dt=0.05, base_seed=0)
    v0 = lyapunov_value(x0, A.unsqueeze(0))
    vf = lyapunov_value(xf, A.unsqueeze(0))
    print(f"  Lyapunov V : {v0:.3f} → {vf:.4f}  (predicted decay rate {cert.contraction_rate:.2f})")
    print(f"  {analyze_trajectory(tr).summary()}")

    # null block: collapse onto a 2-D invariant manifold
    A2 = torch.diag(torch.tensor([0.0, 0.0, 0.0, -0.9, -0.9]))
    print(f"  null block : {collapse_certificate(A2.unsqueeze(0)).summary()}")
    # a single unstable mode: collapse NOT guaranteed
    A3 = torch.diag(torch.tensor([0.6, -0.9, -0.9, -0.9, -0.9]))
    print(f"  unstable   : {collapse_certificate(A3.unsqueeze(0)).summary()}")


def scenario_anti_collapse() -> None:
    banner("7. Σ₀⁻¹ ANTI-COLLAPSE — persistent excitation escapes the 42-state")
    # degenerate system that froze 40/40 under Σ₀ alone
    m = CIO_SDE(dim=4, ctrl_dim=2, hidden=32)
    for p in m.graph.active.drift_net.parameters():
        torch.nn.init.zeros_(p)
    m.collapse_op = SemanticCollapseOperator()
    m.anti_collapse_op = AntiCollapseOperator(strength=0.5)
    x0 = 0.01 * torch.randn(8, 4)
    s0 = torch.eye(4).expand(8, 4, 4).clone()
    _, _, tr = rollout(m, x0, s0, steps=40, base_seed=1)
    norms = tr.x_norms()
    print(f"  Σ₀ fired   : {len(tr.collapses)}/40 steps (was 40/40 without Σ₀⁻¹)")
    print(f"  ‖x‖        : {norms[0]:.4f} → {norms[-1]:.4f}  (re-excited, escaped collapse)")
    print("  Σ₀⁻¹ injects along null eigenmodes only while proximity p > 0 — "
          "zero cost in healthy regimes.")


def scenario_free_energy() -> None:
    banner("5. FREE ENERGY — convergence objective is wired + differentiable")
    torch.manual_seed(4)
    m = CIO_SDE(dim=4, ctrl_dim=2, hidden=32)
    opt = torch.optim.Adam(m.parameters(), lr=5e-3)
    x0 = torch.randn(16, 4)
    s0 = torch.eye(4).expand(16, 4, 4).clone()

    def objective(seed: int):
        xf, sf, tr = rollout(m, x0, s0, steps=20, base_seed=seed,
                             record=False, accumulate_cost=True)
        return tr.running_cost + free_energy(m, xf, m.pcsf(xf, sf), sf).mean()

    j0 = objective(1).item()
    for e in range(60):
        opt.zero_grad()
        loss = objective(100 + e)
        loss.backward()
        opt.step()
    j1 = objective(1).item()
    print(f"  ∫L dt + F : initial {j0:.3f} → trained {j1:.3f}  "
          f"({'decreased' if j1 < j0 else 'no improvement'})")


if __name__ == "__main__":
    scenario_stability()
    scenario_replay()
    scenario_hot_swap()
    scenario_collapse()
    scenario_certificate()
    scenario_anti_collapse()
    scenario_free_energy()
    print("\n" + "=" * 64)
    print("  CIO SDE demo complete — all scenarios ran.")
    print("=" * 64)
