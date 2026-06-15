# Research Dataset Schema

Defines the row shapes for the Creator Intelligence dataset and how rows are collected and stored. **Schemas describe the shape of data we are allowed to collect — they do not imply the data already exists.** A fresh install has zero rows.

## Storage layout

```
data/creator-intelligence/
├── MANIFEST.json        # { general: <n>, gaming: <n>, edits: <n>, sources: [...], updatedAt }
├── general/*.jsonl      # one GeneralShort per line
├── gaming/*.jsonl       # one GamingShort per line
└── edits/*.jsonl        # one EditEvent per line (continuous learning)
```

JSONL (one JSON object per line) is used so collection can append incrementally and the store can count rows cheaply. `MANIFEST.json` is the authoritative count and **provenance** record — it lists which `source` each batch came from so any displayed aggregate can be traced back.

## `GeneralShort` row

```json
{
  "id": "string (platform:videoId)",
  "platform": "youtube | tiktok | instagram | facebook",
  "source": "string — how this row was obtained (api endpoint / dataset name)",
  "collectedAt": "ISO-8601",
  "title": "string",
  "duration": 0,
  "viewCount": 0,
  "likeCount": 0,
  "commentCount": 0,
  "publishDate": "ISO-8601",
  "category": "string",
  "captionDensity": 0,
  "cutFrequency": 0,
  "zoomFrequency": 0,
  "musicPresence": true,
  "hookLength": 0,
  "hookStyle": "instant_payoff | question | text | shock | reaction | countdown | unknown",
  "retentionIndicators": {}
}
```

Fields like `captionDensity`, `cutFrequency`, `zoomFrequency`, `hookLength` are **measured by analyzing the actual video** (the same ffmpeg pipeline used for uploads) — they are not guessed from metadata. If a row was collected from metadata only (no video access), those fields are `null`, not `0`, so aggregates can exclude them honestly.

## `GamingShort` row

Extends `GeneralShort` with:

```json
{
  "game": "fortnite | cod | warzone | valorant | cs2 | minecraft | rocket_league | apex | league | overwatch | other",
  "momentType": "kill | clutch | fail | funny | reaction | boss | ranked | tournament | unknown",
  "facecamPresent": true,
  "facecamCorner": "top_left | top_right | bottom_left | bottom_right | none",
  "hudComplexity": "low | medium | high | unknown"
}
```

## `EditEvent` row (continuous learning)

Appended locally by the editor every time the operator produces or chooses something. This is first-party data — always legitimate to store.

```json
{
  "id": "string",
  "entryId": "string — links to data/creator/entries/<id>",
  "createdAt": "ISO-8601",
  "kind": "edit | variant_generated | variant_selected | export",
  "features": { "cutFrequency": 0, "captionDensity": 0, "hookLength": 0, "zoomFrequency": 0 },
  "choice": "string — e.g. which variant the user kept",
  "outcome": null
}
```

`outcome` stays `null` until/unless the operator supplies real performance data (e.g. actual views after posting). We never invent it.

## Collection pipeline (credentialed, ToS-respecting)

Collection is **opt-in** and requires real credentials. The store ships empty.

| Adapter | Requires | Notes |
|---|---|---|
| YouTube Data API v3 | `YOUTUBE_API_KEY` | official API, quota-limited; legal for metadata + public stats |
| Local corpus import | a folder of files the operator owns/licensed | analyzes real video; no platform calls |
| Manual CSV/JSONL import | operator-provided file | provenance recorded as the filename |

Targets in the original brief (10,000 general / 5,000 gaming) are **goals**, not preloaded data. Until the manifest shows those counts, the dashboard reports `insufficient_data`. Reaching them depends on the operator providing credentials/corpora and running the collector.

### Hard limits we honor

- Respect each platform's API quota and Terms of Service. No scraping that violates ToS.
- Store only what the API/owner legitimately exposes.
- Record `source` for every batch so any aggregate is auditable.

## Sufficiency thresholds (consumed by scoring)

| Use | Constant | Default |
|---|---|---|
| Distribution report (Phase 2) | `MIN_ROWS_FOR_DISTRIBUTION` | 200 |
| Population scoring (Phase 5) | `MIN_ROWS_FOR_SCORING` | 500 |
| Per-game gaming aggregates | `MIN_ROWS_PER_GAME` | 50 |

Below threshold → `insufficient_data` with `have`/`need` so the UI can show progress ("142 / 200 rows toward research-backed pacing").
