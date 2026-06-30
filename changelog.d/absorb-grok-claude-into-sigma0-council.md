### Absorb the Grok/Claude trader council into the Σ₀ council

The trader had two decision layers stacked: a Σ₀ EV gate (`convergence_ev.py`) over Riley's
signals, and — after it — a separate **Claude gate** (`agent_claude_decision`) that could HOLD a
trade the EV had already approved. Grok and Claude's convictions were also merged into one opaque
`llm` signal (weight 0.18), so the council couldn't tell which model actually predicted wins.

This folds both LLMs into the single Σ₀ council:

- **`llm` → `grok` + `claude`** as two first-class council signals (`WEIGHTS` split 0.09 / 0.09,
  total influence unchanged). `sigma0-trader-council.js` already grades `r.signals` dynamically, so
  the per-signal realized-edge table now reports Grok and Claude **separately** and each gets
  re-weighted on its own measured edge. `llm_conf` stays a back-compat alias → `grok_conf`.
- **Claude's veto is stripped.** The Σ₀ EV is now the sole ENTER/SKIP authority. After Claude
  returns, the council **re-scores** the EV with both grok + claude convictions (Claude BUY/SELL
  agreeing with direction → 78, HOLD → 35 lean-against, opposing → 15) and that combined EV decides.
  A Claude HOLD no longer kills a +EV trade — it just lowers `p_win`. Portfolio risk stays enforced
  downstream by `agent_risk_manager` (Claude's HOLD was redundant with it).
- `SIGMA0_EV=0` restores the legacy Claude-as-hard-gate behavior.

The Grok-only pre-screen (Claude neutral) still runs first as a token-saver. Tests:
`tests/test_convergence_ev.py` pins the split (grok/claude graded separately, Claude conviction moves
`p_win`, `llm_conf` back-compat) — 8 passed.
