# Lantern Dreamer Notebook v0 Release

Generated: 2026-05-31
Status: candidate release — local-first, human-approved external announcement required

## What exists now

Lantern Dreamer Notebook v0 adds a small, truthful release surface for private dream and note capture.

## Web surface

Open locally:

```text
http://127.0.0.1:4177/courtney.html
```

Features:

- Courtney notebook capture page
- Dream and note entry types
- Tag input
- Recall/search
- Local JSONL storage

Storage path:

```text
data/dreamer/notebooks/courtney.jsonl
```

## Discord bot commands

The Lantern Discord lounge bot now recognizes these commands in the allowlisted channel:

```text
!dream <text>
!note <text>
!recall [search]
```

Discord entries are stored per Discord user ID, not globally.

Storage pattern:

```text
data/dreamer/notebooks/discord-<author-id>.jsonl
```

## Boundaries

This release does not claim:

- medical memory support
- therapy or clinical use
- cloud sync
- account authentication
- encrypted storage
- automatic Discord posting without bot credentials and operator approval
- GitHub release publishing without a real commit/tag/PR action

## Announcement draft

```text
Lantern Dreamer Notebook v0 is ready for pilot review.

It is a private local-first notebook for dream capture, notes, receipts, and recall.

Available surfaces:
- Lantern Garage web: /courtney.html
- Lantern Discord bot: !dream, !note, !recall

Initial pilot user: Courtney.

Boundaries: local-first v0, no medical/therapy claim, no cloud sync claim, and no automatic external posting without operator approval.
```

## Release checklist

| Gate | Status |
|---|---|
| Web page exists | yes |
| Local API exists | yes |
| Discord commands exist | yes |
| Syntax validation | passed |
| Convergence loop | passed |
| GitHub commit/tag | pending human approval |
| Discord announcement | pending bot credentials + human approval |
