# Dream Removal Report — Create Dashboard

**Date:** 2026-06-18
**Scope:** Surgical removal of the "New Dream Entry" journal feature from the Create Dashboard (`create.html`) only.
**Result:** ✅ Dream functionality fully removed from the Lantern-OS Create Dashboard.

---

## What was removed

The Create Dashboard embedded a **Dream Journal quick-compose** feature (added in PRs #613/#616/#618): a "✦ New Dream Entry" card with templates, markdown preview, autosave, a **Save to Journal** action (POST `/api/dream/create`), and a post-publish **"Published to Dream Journal"** share panel. This was the only Dream entity on the Create screen — there was no separate Dream tile, modal, route, or feature flag. All of it has been removed.

## Files modified

| File | Change |
|---|---|
| `apps/lantern-garage/public/create.html` | **−364 lines, 0 added.** Removed 1 HTML block, 2 CSS blocks, 1 JS IIFE. |

## Files deleted

**None.** The feature was self-contained inline in `create.html`; no standalone component/route files existed to delete.

## Removed in detail

**HTML**
- `#journal-compose` — "New Dream Entry" card: template `<select>` (Dream Log / Gratitude / Idea / Reflection / Story Seed), markdown editor `<textarea>`, Preview toggle, autosave badge, Clear / **Save to Journal** buttons.
- `#share-panel` — "✓ Published to Dream Journal" post-publish panel (copy link, X / Reddit / Email share intents).

**CSS** (all journal/share-only, verified unused elsewhere on the page)
- `.journal-compose`, `.journal-compose-header`, `.journal-compose-footer`, `.journal-editor`, `.journal-word-count`, `.journal-actions`
- `.autosave-badge` (+ `.saved` / `.saving`), `.template-select`, `.btn-icon`, `.editor-wrap`, `.md-preview` (+ children)
- `.share-panel`, `.share-panel-header`, `.share-panel-body`, `.share-link-input`, `.share-intents`, `.share-intent`

**JavaScript** — the entire "Dream Journal Quick-Compose" IIFE
- `applyTemplate()`, `renderPreview()`, `togglePreview()`, `updateWordCount()`, `journalClear()`, `journalSave()`, `showSharePanel()`, `copyShareLink()`
- `TEMPLATES` map, draft autosave (`localStorage` `lantern-journal-draft`), Ctrl/⌘+S handler

## Routes removed

**None.** No route was Dream-Dashboard-specific. The `/api/dream/create` endpoint still exists for the standalone Dream Journal app; it is simply no longer called from the Create Dashboard.

## Imports removed

**None.** The feature used no module imports — it was inline `<style>`/`<script>` and `fetch()` calls.

## Remaining Create Dashboard entries

After cleanup the Create Dashboard (`/create.html`) presents **only creator/research workflows**:

1. **Creator Dashboard** banner (Upload • Analyze • Edit • Export)
2. **Upload Video** card — "Drop a video to start a project" / Choose Video (Σ₀ Shorts pipeline entry; auto-named project → opens `entry.html` workspace)
3. **Recent Projects** — creator project list
4. **Research Library** — PDF drop zone feeding the Knowledge Center

No Dream cards. No Dream placeholders. No hidden Dream routes. (Verified: 0 journal/share-panel/"New Dream Entry" matches in `create.html`; `<script>` tags balanced 5/5; no console errors on load.)

## Deliberately preserved (out of scope)

These are **not** part of the Create Dashboard and were intentionally left untouched:

- **Top-nav "Journal" link** (`<a href="/dream-chat.html">`) — site-wide navigation present on every page; it points to the standalone Dream Journal app, which is Lantern OS's core product. Removing it would break navigation consistency (req: "keep existing navigation structure"). *If you want this nav link gone too, say so — it's a one-line change applied across the shared nav.*
- **`/api/dreamer/upload`** — the **video** upload backend used by the creator flow (`uploadAndOpen()`); "dreamer" is the storage layer name, not the journal.
- **Standalone Dream Journal** (`dream-chat.html`, `/api/dream/create`, dreamer-store, agent personas) — the app's primary product, unrelated to the Create screen.

---

**Confirmation:**

> Dream functionality fully removed from Lantern-OS Create Dashboard.
