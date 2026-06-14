# Convergence IO — Agent Handoff
# Date: 2026-06-14
# For: Gemini / Codex / future Claude lanes
# Status: authoritative

## Two meanings of "Convergence IO" — do not confuse them

**1. Symbolic routing engine (narrative layer)**
Grammar: Garden → Convergence IO → !three-doors → Sigil → Restaurant
Lives in: dream-chat.js, csf-memory.js, csf/ingest docs
Touch this only for dream-chat or door routing tasks.

**2. Mathematical model (Kalshi / market layer)**
Sigma0 collapse certificate — Lyapunov test on price trajectories
Source: src/cio_sde.py -> collapse_certificate(A)
Usage: kalshi_cio_backtest.py, kalshi_tightband_analysis.py
Certifies whether a price series is CONTRACTING (mean-reverting) or DIVERGING (trending)
This layer is about prediction markets, not dreams.

---

## Impossibility Engine quick reference

File: apps/lantern-garage/lib/impossibility-engine.js
Route: GET /api/trading/kalshi/impossibility-deck

State space: probability interval [lo, hi] over P(YES) in [0, 100].
Width <= 15 = DETERMINED. Width <= 40 = CONFIDENT. Width > 40 = UNCERTAIN.

Active constraints (C1-C6):
  C1 price      — market consensus narrows to [yesAsk +/- buffer]
  C2 spread     — tight spread = strong signal; wide = weak
  C3 momentum   — recent tick direction shifts interval
  C4 urgency    — <=5m to close: price IS truth (collapse to +/-4)
  C5 volume     — high volume trusts price more; thin widens
  C6 complement — YES+NO=100c check; dislocation widens

C7 cioConstraint — WIRED, EXCLUDED from DEFAULT_CONSTRAINTS
  Measured 40% direction accuracy on 20 resolved June 13 MLB markets.
  AR(1) is an anti-pattern on trending markets. See issue #424.
  Activate for experiments: createKalshiEngine([cioConstraint])
  Market object needs: market.cio = { has_signal, p_star (0-1), edge }
  Cache: data/kalshi/cio-trajectory-cache.jsonl

---

## Training data pipeline

Tight-band files: data/kalshi/tight-band-*.jsonl
  - 6,090 timestamps x 96 markets @ 6-second resolution (June 13 = 1.0 GB)
  - Schema: { "ts": "...", "snapshot": { "markets": [ { ticker, yes_ask (cents), no_ask (cents), volume, close_time, ... } ] } }
  - Top-level "markets: 0" is an artifact — real data is in snapshot.markets

Run analyzer:
  python experiments/kalshi_tightband_analysis.py
  python experiments/kalshi_tightband_analysis.py data/kalshi/tight-band-2026-06-13.jsonl

Run CIO backtest (synthetic, proves mechanics):
  python experiments/kalshi_cio_backtest.py

Run evaluator on price-snapshots:
  python experiments/kalshi_evaluate.py

---

## What NOT to re-derive

- price-snapshots.jsonl is flat (pre-game, ~0 movement). CIO finds no edge. Expected.
- AR(1) accuracy = 40%: documented in data/kalshi/cio-train-report.json. Do not repeat.
- Tight-band schema: documented above. Do not re-discover field names.
- C7 exclusion: AR(1) anti-pattern on trend markets. In impossibility-engine.js comments.

---

## Open issues

  #424 — Replace AR(1) with momentum-aware trend extractor (divergence gate)
  #425 — Schedule tightband_analysis.py daily, build accuracy log
  #426 — C7 activation criteria: >=55% accuracy, <=40% lead-time

Most impactful: #424. The fix is ~3 lines in kalshi_cio_backtest.py:
  Change: if not cert.guaranteed: return price_now, False  (phi < 1)
  To:     if phi < 1.0: return price_now, False             (mean-reverting = no signal)
          p_terminal = 1.0 if (phi - 1) > 0 else 0.0       (trend to endpoint)
          return p_terminal, abs(p_terminal - price_now) > EDGE_THRESHOLD

---

## Convergence IO engine

  python src/convergence_io_engine.py health   # is server up?
  python src/convergence_io_engine.py inspect  # slots + metrics
  python src/convergence_io_engine.py loop     # 20-phase tesseract loop

Current state: { ok: false, issues: ["no active slots", "listener stale"] }
Server is up (http ok). Normal when no agents running.

---

## PR lane discipline

Claude lane (claude/) is blocked by PR #378. Check before branching:
  gh pr list --state open
Issues #424-426 should go to gemini/ or codex/ lanes.
