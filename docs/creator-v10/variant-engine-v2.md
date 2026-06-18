# VariantEngineV2

Generates up to five edit variants (A–E) from one analyzed upload, each differing along controlled dimensions, then **ranks** them. Ranking is honest: it reports prediction confidence as `insufficient_data` until the dataset crosses thresholds.

## Variation dimensions

Each variant is a deterministic recipe over real analysis output (HighlightTimeline, SafeZones, events):

| Dimension | Options |
|---|---|
| hook | instant_payoff · cold_open · countdown · question_text |
| caption style | (any style id from CaptionEngineV3) |
| cut timing | tight · medium · loose (derived from highlight density) |
| music timing | beat_sync · ambient · none |
| zoom timing | on_event · steady · punch_in |
| ending | hard_cut · loop_back · cta |

Default A–E presets cover a spread (e.g. A = tight/instant_payoff/beat_sync, E = loose/question/ambient). Recipes are stored so a chosen variant is reproducible.

## Variant object

```json
{
  "id": "variantA",
  "recipe": { "hook":"instant_payoff", "captionStyle":"mrbeast_bold", "cut":"tight",
              "music":"beat_sync", "zoom":"on_event", "ending":"hard_cut" },
  "renderPath": null,
  "prediction": { "status": "insufficient_data", "have": 0, "need": 500 }
}
```

`renderPath` is `null` until the variant is actually rendered (ffmpeg). The dashboard shows "Not rendered" — not a fake thumbnail.

## Ranking & prediction

Ranking calls `scoring/score-engine.js`:

- **Dataset ≥ `MIN_ROWS_FOR_SCORING`:** each variant gets `{ status:"ok", value, basis }` for `completionRate` / `viralScore` / `shareRate`, computed from how similar real high-performing rows were edited. Variants sort by `viralScore`.
- **Dataset below threshold:** every variant returns `{ status:"insufficient_data", have, need }`. The UI ranks by **deterministic heuristic order** (e.g. tighter cuts first for gaming) and clearly labels it *"heuristic order — no performance data yet"*, **not** a predicted percentage.

This is the crux of the honesty rule for variants: we will happily *generate* five edits with zero data, but we will not *claim* "Variant B: 91% completion" unless a real dataset supports it.

## Continuous learning loop

When the operator keeps a variant, `training/learning-store.js` appends a `variant_selected` `EditEvent`. These first-party signals accumulate locally and, once past threshold, let the score engine personalize ranking to the operator's own results — still data-backed, still auditable.

## Feature flag

Behind `variantEngineV2` (`LANTERN_CI_VARIANT_V2`, default off). When off, the editor produces the single highlight render plus the existing A/B/C render slots.

## Implementation steps

1. Recipe presets A–E + reproducible recipe storage.
2. Renderer that applies a recipe via ffmpeg (cut list, zoom keyframes, music mix, caption burn).
3. Ranking via `score-engine` with the `insufficient_data` path wired to the UI.
4. `variant_selected` learning hook.
