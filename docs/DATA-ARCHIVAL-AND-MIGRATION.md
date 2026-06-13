# Data Archival & Migration Plan (2026-06-10)

## What was done

- **Repo archival (commit aaae817):** 3,665 stale files (untouched > 3 days) moved out of
  the repo to `D:\tmp\archive\` — the in-repo `archive/` tree (~3,400 files) and
  `data/reports/` (unreferenced). ~624K lines removed from version control.
- **Kept live:** `data/ingest/`, `data/rag-intake/` (referenced by running code),
  all tracked `data/*.json` state files.
- **Local-only artifacts** (gitignored, never pushed): `alex-imagniverse.csf`,
  `alex-realworld.csf`, the 23 MB founder video (archived to
  `D:\tmp\lantern-os-archive-2026-06-10\`).

## Staleness policy going forward

Files in `data/`, `archive/`, or `models/` not committed or modified in > 3 days and
not referenced by code are candidates for `D:\tmp\archive\<date>\`. Check references
with `git grep <path>` before moving. Untracked large blobs (> 5 MB) should never be
committed — gitignore them and archive to `D:\tmp`.

## Google Drive migration (pending — access limitation)

The Drive MCP connector currently has **per-file scoped access**: only two documents
are visible ("Kingdome of Hearts — Master Lore", "Silverheart Whisperwood"). The
research-paper and data archives described in the split-data-model cannot be
enumerated or moved through it.

Recommended steps (manual or after widening connector scope):

1. **Keep in Drive (essential):** real/private datasets, encrypted exports, anything
   referenced by the split-data-model (repo = code + sanitized examples; Drive = real
   data).
2. **Migrate out (non-essential):** downloaded papers and public PDFs → local
   `D:\tmp\archive\gdrive-papers\` (they are re-downloadable; Drive quota is better
   spent on irreplaceable data); generated reports/exports older than 30 days → same
   archive; duplicates of files already in `D:\tmp` or the repo → delete.
3. **Re-scope the connector** (grant folder-level access) if agent-driven migration is
   wanted; until then this section is a checklist for a manual pass.
