# Creator Dashboard V10 — Research-Driven Autonomous Shorts Engine

**Status:** Architecture + incremental implementation (foundation pass)
**Branch:** `feature/creator-intelligence-v10`
**Builds on:** V9 Creator Suite (`apps/lantern-garage/lib/highlight-engine.js`, `safe-zone-detector.js`, `caption-engine.js`, `entry-store.js`, `job-queue.js`, `job-worker.js`)

---

## Mission

Turn the Lantern Creator Dashboard into an AI video editor that produces gaming Shorts able to compete with top-performing YouTube Shorts / TikTok / Reels — driven by **measurable** retention, engagement and pacing signals rather than subjective editing rules.

## The Non-Negotiable Rule (read first)

> **Do not fabricate analytics, retention scores, or research findings.**

Every number the dashboard shows must be traceable to one of exactly two sources:

1. **Actual video analysis** of a file the user uploaded (ffmpeg/ffprobe output), or
2. **Actual collected dataset rows** stored under `data/creator-intelligence/`.

When neither exists, the system returns a structured `insufficient_data` result and the UI renders **"Insufficient data"** — never an invented score. This is enforced in code by `src/creator-intelligence/scoring/` guards, not by convention. See [creator-intelligence-architecture.md](creator-intelligence-architecture.md).

What this means in practice:

- We do **not** ship claims like "trained on the 10,000 most popular Shorts" unless those rows physically exist in the dataset store and the manifest counts prove it.
- A freshly-installed Lantern has an **empty** dataset. The honest state is `datasetSize: 0` and `status: "insufficient_data"` everywhere that depends on research.
- Real video analysis (motion/audio/scene/safe-zone/ffprobe) works on day one because it operates on the user's own uploaded file — that is legitimately traceable.

## Current State (V9 → V10 gap)

| Capability | V9 today | V10 target |
|---|---|---|
| Highlight detection | ✅ Real ffmpeg motion/audio/scene (`highlight-engine.js`) | Keep; add reaction/speech signals |
| Safe zones | ⚠️ Heuristic, **bug: detected zones discarded** (`safe-zone-detector.js:238`) | `SafeZoneDetectorV2` — fix bug, multi-frame sampling, crop priority |
| Captions | ✅ Style library + highlight-driven (`caption-engine.js`) | `CaptionEngineV3` — event taxonomy, 50+ styles, effects |
| Variants | Partial (A/B/C renders referenced in `entry-store`) | `VariantEngineV2` — A–E, ranked (insufficient-data aware) |
| Research dataset | ❌ none | `src/creator-intelligence/dataset/` — schema + honest store |
| Viral/retention scoring | ❌ none (or fabricated) | `scoring/` — data-backed or `insufficient_data` |
| Export validation | ❌ none | `ExportValidator` — real ffprobe gates |
| Continuous learning | ❌ none | `training/` — append edits/variants/selections |

## 8-Phase Plan

### Phase 1 — Research dataset infrastructure
Build `src/creator-intelligence/dataset/` (schema + store) and `data/creator-intelligence/` storage. **No fabricated rows.** Collection adapters require real API credentials (YouTube Data API v3, etc.) and respect each platform's ToS; absent credentials, the store stays empty and reports `0`. See [research-dataset-schema.md](research-dataset-schema.md).

### Phase 2 — Reverse-engineer viral editing (report generator)
`analysis/` computes hook-style / caption / camera-movement / timing distributions **from whatever rows actually exist**. With an empty dataset the report is `insufficient_data`. The report generator never hardcodes "best cut rate = X".

### Phase 3 — Facecam preservation (`SafeZoneDetectorV2`)
Fix the V9 discard bug, sample multiple frames, emit protected regions with a strict crop priority (facecam → crosshair → HUD → action). See [safe-zone-v2.md](safe-zone-v2.md).

### Phase 4 — Intelligent captions (`CaptionEngineV3`)
Event taxonomy (kill, multi-kill, clutch, near-death, funny, victory, loss, reaction), dynamic caption text, 50+ styles, visual effects. See [caption-engine-v3.md](caption-engine-v3.md).

### Phase 5 — Variant generation (`VariantEngineV2`)
Generate A–E variants differing on hook / caption style / cut timing / music timing / zoom timing / ending. Ranking uses the scoring engine — and reports `insufficient_data` confidence when there is no dataset to predict from. See [variant-engine-v2.md](variant-engine-v2.md).

### Phase 6 — Dashboard integration
Rename "Content Creator" → "Creator Dashboard". Tabs: Projects, Analysis, Variants, Captions, Exports, Research. Per project: thumbnail (first frame, fallback 2s frame), inline players (original + edited + variants), analysis view (highlights, facecam region, safe zones, predicted retention or "insufficient data", caption timeline).

### Phase 7 — Quality validation (`ExportValidator`)
Before any export: ffprobe-verify resolution 1080×1920, fps, audio present, duration 15–60 s, captions actually rendered. Fail → export blocked with a concrete reason. See [export-validator.md](export-validator.md).

### Phase 8 — Continuous learning
Append every edit, variant, score and user selection to `data/creator-intelligence/edits/`. This local signal feeds future scoring once enough rows accumulate — and until then, scoring honestly reports low confidence.

## Feature Flags

All V10 behavior ships behind flags in `src/creator-intelligence/dataset/feature-flags.js` (env-overridable). Default **off** for anything unproven so the stable dashboard is never destabilized:

| Flag | Env var | Default | Gates |
|---|---|---|---|
| `creatorIntelligence` | `LANTERN_CI_ENABLED` | off | whole subsystem |
| `safeZoneV2` | `LANTERN_CI_SAFEZONE_V2` | off | new detector |
| `captionEngineV3` | `LANTERN_CI_CAPTION_V3` | off | new caption engine |
| `variantEngineV2` | `LANTERN_CI_VARIANT_V2` | off | A–E variants |
| `exportValidator` | `LANTERN_CI_EXPORT_VALIDATOR` | **on** | ffprobe gates (safe to enable) |
| `researchReport` | `LANTERN_CI_RESEARCH_REPORT` | off | reverse-engineer report |

## Deliverables (this doc set)

- `creator-dashboard-v10-plan.md` (this file)
- [creator-intelligence-architecture.md](creator-intelligence-architecture.md)
- [research-dataset-schema.md](research-dataset-schema.md)
- [safe-zone-v2.md](safe-zone-v2.md)
- [caption-engine-v3.md](caption-engine-v3.md)
- [variant-engine-v2.md](variant-engine-v2.md)
- [export-validator.md](export-validator.md)

## Definition of "production-ready"

The Creator Dashboard is production-ready when:

1. Every displayed metric is traceable (analysis output or dataset row) — verified by the `insufficient_data` guards.
2. Exports always pass `ExportValidator` or are blocked with a reason.
3. Facecam/HUD are never cropped (SafeZoneDetectorV2 + crop priority).
4. The research report reflects only rows that exist.
