# Lantern Dreamer Notebook v0 Announcements

Generated: 2026-05-31
Status: staged for human-approved publication

## GitHub release title

```text
Lantern Dreamer Notebook v0
```

## GitHub release body

```markdown
# Lantern Dreamer Notebook v0

Local-first dream and note capture for Lantern OS.

## What shipped

- Courtney notebook web surface at `/courtney.html`
- Local Dreamer API at `/api/dreamer`
- Per-user JSONL notebook storage
- Dream capture
- Note capture
- Recall/search
- Discord bot commands: `!dream`, `!note`, `!recall`

## Storage

Web pilot user:

```text
data/dreamer/notebooks/courtney.jsonl
```

Discord users:

```text
data/dreamer/notebooks/discord-<author-id>.jsonl
```

## Validation

- `npm run check` in `apps/lantern-garage`: passed
- `python -m py_compile src\discord_lounge_bot\bot.py`: passed
- `scripts/Invoke-LanternConvergenceLoop.ps1`: passed

## Boundaries

This is a local-first v0. It does not claim medical memory support, therapy, clinical use, cloud sync, encrypted storage, or automatic public posting. Discord command use requires the allowlisted Lantern Discord bot channel and configured bot token.
```

## Discord announcement

```text
Lantern Dreamer Notebook v0 is ready for pilot review.

What shipped:
- Courtney notebook web page: /courtney.html
- Private local dream + note capture
- Recall/search
- Discord commands: !dream, !note, !recall

Boundary: local-first v0 only. No medical/therapy claim, no cloud sync claim, no encrypted-storage claim, and no automatic public posting beyond this approved announcement.

Initial pilot user: Courtney.
```

## Publication gates

| Gate | Status |
|---|---|
| Local implementation | passed |
| Syntax validation | passed |
| Convergence validation | passed |
| GitHub commit/push | pending human approval |
| GitHub release/tag | pending human approval |
| Discord post | pending Discord token/channel + human approval |
