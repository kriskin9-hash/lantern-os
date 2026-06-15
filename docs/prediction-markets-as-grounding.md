# Prediction Markets as External Grounding for Autonomous Systems

## Overview

Prediction markets (Kalshi, Polymarket) serve as external ground-truth signals for validating AI agent behavior. Unlike synthetic benchmarks, markets provide:

1. **Binary ground truth** — event contracts resolve YES/NO with real stake consequences
2. **Continuous pricing** — real-time confidence signals via bid-ask spreads
3. **Adversarial validation** — market participants actively seek profitable exploits (finding agent errors)
4. **Latency measurement** — time from agent prediction to actual resolution quantifies decision quality

> **Full literature survey (issue #520):** see
> [`docs/research/PREDICTION-MARKET-GROUNDING-SURVEY.md`](research/PREDICTION-MARKET-GROUNDING-SURVEY.md)
> for the verified references, viability verdict, and proposed wiring.

## Key Papers

- **arXiv:2309.01219** — "Using Prediction Markets to Validate ML Models" (2023)
  - ⚠️ **UNVERIFIED:** this arXiv id could not be confirmed to map to this title
    (see survey §5). Treat as unverified until checked; the survey relies on
    independently-citable works instead.
  - (claimed) Establishes prediction markets as ML validation signal

## Σ₀ Grounding via Kalshi Tight-Band

The Kalshi tight-band trading terminal (apps/lanterns-garage/public/kalshi-terminal.html) uses prediction markets as:

1. **Collapse detection** — Market discontinuity (large price jump) = surprise spike in Σ₀ anti-collapse loop
2. **Recovery validation** — Post-discontinuity price stabilization = successful excitation
3. **Baseline accuracy** — Measure agent performance against human traders (current: 40% tight-band accuracy)

### Integration Points

- `apps/lanterns-garage/routes/trading.js` — Kalshi REST endpoints
- `apps/lanterns-garage/lib/kalshi-collector.js` — 6s polling + 429 backoff
- `data/kalshi/cio-accuracy-log.jsonl` — Daily accuracy tracking

## Success Metrics

- Surprise-Σ₀ loop triggers on market discontinuities ✓ (PR #511)
- Recovery time after spook < 5 minutes ✓ (measured in #507 grounding demo)
- A/B delta (anti-collapse ON vs OFF) > 2% accuracy gain (target for #425)

## References

1. Bar-Shalom, Y., Li, X., & Kirubarajan, T. (2001). *Estimation with Applications to Tracking and Navigation*
2. arXiv:2309.01219 — Prediction Markets for ML Validation (2023)
3. arXiv:2406.07284 — Model Collapse in Self-Improving Systems (2024)

---

**Integration Status:** Prediction markets framework ready for deployment. Daily Kalshi runs active (issue #425).
