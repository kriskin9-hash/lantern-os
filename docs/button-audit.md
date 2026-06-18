# Button Audit — Creator Dashboard & Entry Page

> Sigma0 Maintenance Cycle — 2026-06-15
> Audits all interactive buttons for correct wiring, disabled-state handling, and API integration.

## Summary

| Page | Buttons | Pass | Fail | Notes |
|------|---------|------|------|-------|
| `create.html` | 4 | 4 | 0 | All wired correctly |
| `entry.html` | 13 | 13 | 0 | Fixed in this cycle |

---

## create.html

### Upload Zone

| Button / Control | ID / Selector | Expected Behavior | Status |
|-----------------|---------------|-------------------|--------|
| Drop zone click area | `#upload-zone` | Opens file picker via `#file-input` | ✓ PASS |
| Hidden file input | `#file-input` | Accepts `.mp4, .mov, .avi, .mkv, .webm` | ✓ PASS |
| Save Project | `#submit-btn` | Validates title + file, calls `POST /api/creator-entries` | ✓ PASS |
| Clear Form | `button:has-text("Clear Form")` | Resets title, description, file state | ✓ PASS |

**Notes:** Form validation prevents submit when title is empty. File size is validated client-side. No disabled-state bugs observed.

---

## entry.html — Workspace Actions

| Button | ID | onclick | API Called | Status |
|--------|----|---------|-----------|--------|
| Analyze Highlights | `#wa-analyze` | `runAnalyze()` | `POST /api/creator/analyze` | ✓ PASS |
| Generate Variants | `#wa-variants` | `runRegenVariants()` | `POST /api/creator-entries/:id/regenerate-variants` | ✓ PASS |
| Generate Captions | `#wa-captions` | `runRegenCaptions()` | `POST /api/creator-entries/:id/regenerate-captions` | ✓ PASS |
| Detect Safe Zones | `#wa-safezones` | `runSafeZones()` | `POST /api/creator/safe-zones` | ✓ PASS |
| Render Shorts | `#wa-render` | `runRenderShorts()` | `POST /api/creator/export` | ✓ PASS |

**Disabled-state behavior:** All `wa-btn` buttons are disabled (`btn.disabled = true`) at the start of a job run and re-enabled on completion or error. Confirmed in `runAnalyze` / poll loop.

---

## entry.html — Tabs

| Tab Button | onclick | Target Panel | Status |
|-----------|---------|-------------|--------|
| Overview | `switchTab('overview')` | `#overview` | ✓ PASS |
| Analysis | `switchTab('analysis')` | `#analysis` | ✓ PASS |
| Renders | `switchTab('renders')` | `#renders` | ✓ PASS |
| Metadata | `switchTab('metadata')` | `#metadata` | ✓ PASS |

---

## entry.html — Per-Render Controls

| Button | onclick | Behavior | Status |
|--------|---------|----------|--------|
| Re-render | `reRender(renderKey)` | Queues new export job | ✓ PASS |
| Delete render | `deleteRender(renderId)` | `DELETE /api/creator-entries/:id/render/:renderId` | ✓ PASS |
| Export Variant | `exportVariant(variantId)` | Queues export for selected variant | ✓ PASS |
| Download artifact | `.download-btn` | Direct `<a download>` link to `/media/*` path | ✓ PASS |

---

## TaskProgressPanel (TPP) — Fixed This Cycle

The prior implementation used a simple `<progress>` element that froze at 10% (the first callback from the highlight engine) and never advanced. This was replaced with the TaskProgressPanel system:

| TPP Element | ID | Purpose | Status |
|-------------|-----|---------|--------|
| Container | `#tpp` | Hidden until job starts | ✓ PASS |
| Fill bar | `#tpp-fill` | Smooth interpolated progress, easing at 0.12/tick | ✓ PASS |
| Pct label | `#tpp-pct` | Live "45%" display | ✓ PASS |
| Stage list | `#tpp-stages` | ✓/⟳/○ per stage with weight-based progress | ✓ PASS |
| Live stats | `#tpp-live` | Shows "Analyzed 12s / 30s" during frame scan | ✓ PASS |
| ETA display | `#tpp-eta` | Counts down, hides when < 3s remaining | ✓ PASS |
| Log toggle | `#tpp-log-toggle` | Expands/collapses analysis log | ✓ PASS |
| Log container | `#tpp-log` | Scrollable, capped at 200 entries server-side | ✓ PASS |
| Done panel | `#tpp-done` | Shown on success with runtime + segment count | ✓ PASS |
| Fail panel | `#tpp-fail` | Shown on failure with stage + error message | ✓ PASS |

**Root cause of "frozen at 10%":** `analyzeVideoForHighlights` fires only 4-5 progress callbacks total (8% → 12% → ~50% → 66%). The new TPP interpolates smoothly between these values using `_smoothPct += diff * 0.12` at 80ms intervals, so the bar advances continuously even when the underlying engine is silent.

---

## Inline Title Rename

| Interaction | Expected | Status |
|-------------|----------|--------|
| Click `#entry-title` | Input field appears in-place | ✓ PASS |
| Enter key | Saves via `PUT /api/creator-entries/:id` | ✓ PASS |
| Escape key | Restores original title, no API call | ✓ PASS |
| Blur (click away) | Saves via PUT | ✓ PASS |
