---
author: Alex Place
created: 2026-07-02
---

# Trader EV layer + real-money readiness — Σ₀ review (2026-07-02)

**Question:** what actually makes the AI trader produce good *training* results and get *ready
to trade real money*? Evidence-based review of the existing machinery.

## Finding 1 — the trader already learns; the bottleneck is DATA, not code

- **The EV decision is a learned, weighted vote.** `convergence_ev.score_convergence` computes
  `p_win` from weighted signals, then enters iff `EV(R) = p_win·target_R − (1−p_win)·1R ≥ EV_MIN
  (0.15R)` and `p_win ≥ P_MIN`. *(high; `src/trading_agents/convergence_ev.py:15,252`.)*
- **The weights adapt from realized edge, live.** `agents.py:7490-7504` calls
  `convergence_ev.adapt_weights(rows)` on graded convergence rows (from the Σ₀ trader council)
  and feeds the adapted weights back into `score_convergence` — a closed learning loop
  (`per_signal_lift` → realized per-signal edge → ±-capped weight nudge). *(high; those lines.)*
- **So "training" = accumulating clean graded outcomes.** But there are only **84** rows in
  `data/convergence/trader-outcomes.jsonl`, many of them warmup + the churn round-trips from the
  5-instance collision. `adapt_weights` has a `min_rows` gate, so a thin/polluted set barely
  moves the weights. *(high; `wc -l`, warm_sigma0_council provenance.)*

**Implication:** the single biggest lever for good training results was **stopping the churn**
(done — one instance now). Every clean, single-instance graded outcome from here is real signal
the weight-adapter can use. No new learning code is needed; clean forward data is.

## Finding 2 — the go-live gate exists but is invisible and unenforced

- `agents.py get_graduation_analysis()` already evaluates live-readiness: **30+ days of data,
  20+ trades, win-rate ≥ 55%, Sharpe ≥ 1.0**, returning `{ready, meets_trades, meets_winrate,
  meets_sharpe, …}`. *(high; `agents.py:~933`.)*
- It is **not surfaced anywhere** — no `cli.py` action, no node endpoint, no UI card — and
  nothing gates the switch off `paper-api.alpaca.markets` on it. *(high; grep found no callers.)*

## Recommendations (prioritized)

1. **Let it run clean and accumulate graded outcomes.** The churn fix + single-instance lock is
   the precondition; now the paper track record needs to rebuild on clean data before any weight
   adaptation or readiness number means anything. (No code.)
2. **Surface the readiness gate** — add a `cli.py` `graduation` action → `GET
   /api/trading/ai-trader/readiness` → a small card next to the ON/OFF button showing
   trades / win-rate / Sharpe vs the thresholds and a ready/not-ready verdict. Makes "how close
   to real money" observable and turns `get_graduation_analysis` into the explicit go-live gate.
   (Low-risk, read-only.)
3. **Guard the paper→live switch on that gate** — refuse to point at the live Alpaca endpoint
   unless `get_graduation_analysis().ready` is true (+ an explicit operator confirm). Real-money
   safety belongs in code, not memory.
4. **Grade honestly, keep the input clean** — ensure `trader-outcomes.jsonl` only gets
   single-instance, real closed-trade rows from here (the warmup rows are labeled `source:
   warmup-*` and removable), so calibration/Brier and the weight-adapter learn from truth.

## What this review does NOT do

No trading logic changed. This is analysis + a plan; the strategy itself (Riley setups, EV
thresholds, sizing) is unchanged and should only move on measured evidence from clean data.
</content>
