### Flourishing: cross-domain correlation patterns (real, not trivial)

- The home Flourishing panel now surfaces a **cross-domain correlation** — Pearson r across ~200 real countries (World Bank, aggregates filtered) for flourishing-relevant indicator pairs. Replaces the source model's trivial "this fraction isn't 0.5" outliers with genuine couplings, e.g. life expectancy ↔ electricity access (r≈+0.73), child mortality ↔ schooling (r≈−0.71), and a non-obvious life expectancy ↔ renewable-share (r≈−0.55).
- New endpoint `GET /api/flourishing/correlations`. Correlation, not causation — labeled as such; loads separately so the per-country fetch never blocks the belief panel.
