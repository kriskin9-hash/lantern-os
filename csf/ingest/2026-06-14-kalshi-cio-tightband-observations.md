# CSF Ingest — Kalshi x Convergence IO Tight-Band Observations
# Date: 2026-06-14
# Status: complete — experiments run, issues logged, memory updated

## What happened

Session extended the Kalshi training data pipeline from single-snapshot pre-game data
to the full tight-band trajectory dataset. The Impossibility Engine gained a C7 slot
wired for CIO convergence, then was immediately grounded in real measurement.

---

## Dataset State

| File | Size | Content |
|------|------|---------|
| data/kalshi/tight-band-2026-06-13.jsonl | 1.0 GB | 6,090 timestamps x 96 markets @ 6s |
| data/kalshi/tight-band-2026-06-14.jsonl | 0.6 GB | ~2,700 timestamps x 90 markets @ 6s |
| data/kalshi/price-snapshots.jsonl | small | 199 tickers x 22 timestamps (1-min, pre-game) |
| data/kalshi/cio-trajectory-cache.jsonl | small | 96 rows -- latest CIO result per ticker |
| data/kalshi/cio-train-report.json | small | AR(1) model metrics + tightband_eval block |

---

## Core Finding: CIO AR(1) is the wrong model for game markets

Knowledge = Remaining States After Constraint Elimination.

The AR(1) fixed-point estimator CERTIFIES convergence (|l| < 1 = mean-reverting).
MLB game prices DO NOT mean-revert -- they trend monotonically to 0 or 1.

Therefore S0 fires when the price is wobbling mid-game (apparent mean-reversion in
the noise), then estimates p* ~= mid-game average ~= 0.5, which is anti-correlated
with the actual outcome side.

Measured on 20 resolved games (June 13 tight-band):
- Direction accuracy: 40% (below 50% coin-flip baseline)
- Average lead-time: 67.3% of trajectory elapsed

C7 constraint is wired and exported from impossibility-engine.js but excluded from
DEFAULT_CONSTRAINTS until a momentum-aware model (|l| > 1 gate, trend extrapolation)
replaces the AR(1) fixed-point. See issue #424.

---

## Impossibility Engine: 6 active constraints (C1-C6)

All working. C7 slot exists for future signal. Test solve: DETERMINED | 55% probable,
2 constraints applied (price + volume).

---

## Convergence IO Tesseract connection

The Tesseract epistemics: Knowledge = what remains after all constraints eliminate
impossible states. The CIO measurement session demonstrates the meta-principle:

    Applying a model that assumes the WRONG ATTRACTOR TYPE is itself a constraint
    violation -- it attempts to eliminate states that are actually valid, producing
    negative knowledge (confident wrong answers).

The fix: certify DIVERGENCE from the midpoint, not convergence to a fixed point.
A game price diverging from 0.5 with S0 |l| > 1 is MORE determined -- the valid
state space is SHRINKING toward one endpoint.

---

## Attractor map

| State | Tesseract label | CIO signal |
|-------|-----------------|------------|
| Pre-game (price ~0.50) | UNCERTAIN | |l| < 1, mean-reverting |
| Mid-game, score tied | UNCERTAIN-TRENDING | C3 momentum starts |
| Late game, score decided | CONFIDENT-COMMITTING | C3 large tick; C4 kicks in |
| Near resolution | DETERMINED | C4 collapses to +/-4 |
| Resolved (0.99 or 0.01) | DETERMINED | C4 + C1 lock it |

## Files created this session

- experiments/kalshi_tightband_analysis.py -- sliding-window CIO evaluator + cache
- C7 slot in apps/lantern-garage/lib/impossibility-engine.js (wired, excluded)
- Updated data/kalshi/cio-train-report.json with real backtest block

## Issues logged

- #424 -- CIO C7: replace AR(1) with momentum-aware trend extractor
- #425 -- Tight-band flywheel: schedule tightband_analysis.py daily
- #426 -- C7 activation criteria (>=55% accuracy, <=40% lead-time)
