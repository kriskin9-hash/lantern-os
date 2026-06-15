# Creator Dashboard Audit — Sigma0 Maintenance Cycle

> Sigma0 Maintenance Cycle — 2026-06-15

## Feature Verification Matrix

| Feature | Component | Status | Notes |
|---------|-----------|--------|-------|
| Upload video via drag-drop | `create.html` | ✓ PASS | Drop zone active |
| Upload video via click | `create.html` | ✓ PASS | `#file-input` triggers picker |
| Create project entry | `POST /api/creator-entries` | ✓ PASS | Returns `{ entry: { id, title, ... } }` |
| List recent projects | `GET /api/creator-entries` | ✓ PASS | Sorted by createdAt desc |
| Open project | `entry.html?id=:id` | ✓ PASS | Loads entry detail on open |
| Rename project (inline) | `PUT /api/creator-entries/:id` | ✓ PASS | Persists to disk |
| Delete project | `DELETE /api/creator-entries/:id` | ✓ PASS | Removes from list |
| Analyze Highlights | `POST /api/creator/analyze` | ✓ PASS | Returns `jobId`, begins polling |
| Generate Variants (stored) | `POST /api/creator-entries/:id/regenerate-variants` | ✓ PASS | Requires prior analysis |
| Generate Captions (stored) | `POST /api/creator-entries/:id/regenerate-captions` | ✓ PASS | Requires prior analysis |
| Detect Safe Zones | `POST /api/creator/safe-zones` | ✓ PASS | Writes `safe_zone_report.json` |
| Render Shorts | `POST /api/creator/export` | ✓ PASS | Validates then writes render |
| Job progress tracking | `GET /api/creator/job/:jobId` | ✓ FIXED | Now returns full `toJSON()` with stages/logs/liveStats |
| TaskProgressPanel | `entry.html` | ✓ FIXED | Stage-aware with smooth interpolation |
| Download render | `.download-btn` | ✓ PASS | Direct link to `/media/` |
| Re-render button | `reRender(key)` | ✓ PASS | Queues new export |
| Delete render | `deleteRender(id)` | ✓ PASS | Removes record |
| Export variant | `exportVariant(id)` | ✓ PASS | Requires completed analysis |
| Queue health | `GET /api/creator/queue` | ✓ PASS | Returns `{ pending, processing, stats }` |
| Health check | `GET /api/creator/health` | ✓ PASS | Returns `{ status: "ready" }` |
| Export validation | `ci.validateExport()` | ✓ PASS | Blocks out-of-spec exports (422) with `force` override |
| Thumbnail generation | Background `setImmediate` | ✓ PASS | Non-blocking; updates entry after render |

---

## Job Pipeline — Stage Coverage

The analyze job now reports 8 named stages. The job API includes `stages[]`, `logs[]`, `liveStats{}`, and `etaSeconds` in every poll response.

| Stage ID | Name | Weight | Trigger |
|----------|------|--------|---------|
| `load` | Loading Video | 5% | `onProgress({ statusKey: "loading_video" })` |
| `metadata` | Extracting Metadata | 5% | After load, before scan |
| `frame_scan` | Scanning Frames | 25% | `onProgress({ statusKey: "analyzing_motion" })` |
| `motion` | Motion Analysis | 15% | Progress 15–40% range |
| `highlights` | Detecting Highlights | 15% | `onProgress({ statusKey: "detecting_highlights" })` |
| `ranking` | Ranking Moments | 10% | Progress 66%+ |
| `scoring` | Scoring & Variants | 15% | Auto-started after ranking |
| `saving` | Saving Results | 10% | On `complete()` |

---

## Instrumentation Outputs

### `highlight_debug.json`

Written to `data/creator/analyses/{jobId}-highlight_debug.json` and `data/creator/entries/{entryId}/highlight_debug.json` after each successful analysis.

| Field | Type | Source |
|-------|------|--------|
| `jobId` | string | job.id |
| `videoPath` | string | input param |
| `analyzedAt` | ISO string | new Date() |
| `durationSec` | number \| null | timeline.duration |
| `highlightCount` | number | highlights.length |
| `segments[].score` | number | highlight.score |
| `segments[].signals` | string[] | highlight.tags |
| `segments[].reason` | string | highlight.reason |
| `segments[].motion` | null | honest null (engine doesn't expose per-frame) |
| `segments[].audio_peak` | null | honest null |
| `segments[].speech_energy` | null | honest null |

**Honesty rule:** per-frame signal strengths are marked `null` rather than fabricated. These are a future instrumentation target when the highlight engine exposes them.

### `safe_zone_report.json`

Written to `data/creator/entries/{entryId}/safe_zone_report.json` after each safe-zone detection job.

| Field | Description |
|-------|-------------|
| `enforcement.facecam_visible` | Whether a facecam region was detected |
| `enforcement.facecam_confidence` | Detection confidence 0–1 |
| `enforcement.rejected` | True if confidence < 0.40 (too uncertain to apply crop plan) |
| `enforcement.rejection_reason` | Human-readable rejection explanation |
| `cropPlan` | Encoded crop plan for export (null if rejected) |

---

## Known Limitations (Not Fixed This Cycle)

| Issue | Severity | Reason Not Fixed |
|-------|----------|-----------------|
| `motion`, `audio_peak`, `speech_energy` in debug output are always null | LOW | Requires changes to highlight engine internals (out of scope for maintenance cycle) |
| Variant export doesn't surface frame-level safe-zone map | MEDIUM | Requires export pipeline changes |
| No retry mechanism for failed jobs | LOW | Architecture change; deferred |
| Progress callbacks from engine are sparse (4-5 total) | LOW | Fixed in UI layer (TPP interpolation); engine changes out of scope |

---

## E2E Test Coverage

Playwright tests added at `tests/e2e/creator-dashboard.spec.js`:

- Navigation & page load (4 tests)
- Project create / form reset (2 tests)
- API routes: list, create, get, rename, delete, analyze, job status, queue, health, regen-variants, regen-captions (11 tests)
- Entry page buttons: all 5 wa-btn present, tab switching, TPP DOM elements, title rename, back link (8 tests)
- Dashboard list: entry appears, delete modal cancel (2 tests)

**Total: ~27 tests across 5 suites.**
