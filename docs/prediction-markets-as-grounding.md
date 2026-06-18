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

- **Wolfers, J. & Zitzewitz, E. (2004)** — "Prediction Markets", *Journal of
  Economic Perspectives* 18(2):107–126.
  - ✅ **VERIFIED (2026-06-17, #660).** Canonical reference for prediction-market
    accuracy; grounds the use of markets as an external validation signal.
  - Note: a prior draft cited `arXiv:2309.01219` as "Using Prediction Markets to
    Validate ML Models" — that id is actually a *hallucination survey* and has been
    removed (see survey §5).

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
2. Wolfers, J. & Zitzewitz, E. (2004). Prediction Markets. *J. Economic Perspectives* 18(2):107–126
3. Dohmatob, E. et al. (2024). A Tale of Tails: Model Collapse as a Change of Scaling Laws. arXiv:2402.07043 (ICML 2024)

---

**Integration Status:** Prediction markets framework ready for deployment. Daily Kalshi runs active (issue #425).
