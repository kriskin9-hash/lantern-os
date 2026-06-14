# data/creator-intelligence/

Storage for the Creator Intelligence (V10) dataset and continuous-learning events.

**This directory ships empty.** A fresh install has zero rows. Every count in
`MANIFEST.json` reflects rows that physically exist here — nothing is seeded or
faked. Until rows are collected (with real credentials / owned corpora), the
Creator Dashboard honestly reports **"insufficient data"** for any
population-based metric.

## Layout

| Path | Contents |
|---|---|
| `MANIFEST.json` | authoritative counts + provenance; regenerated on every append |
| `general/*.jsonl` | `GeneralShort` rows (one JSON per line) |
| `gaming/*.jsonl` | `GamingShort` rows |
| `edits/*.jsonl` | first-party `EditEvent` rows (continuous learning) |

Schemas: [docs/creator-v10/research-dataset-schema.md](../../docs/creator-v10/research-dataset-schema.md)

## Provenance rule

Every collected batch records its `source` so any displayed aggregate is
auditable back to where the data came from. Collection respects each platform's
API quota and Terms of Service. No scraping in violation of ToS.

> `*.jsonl` data files are git-ignored (they can be large and may contain
> collected rows). The directory structure, README, and MANIFEST are tracked.
