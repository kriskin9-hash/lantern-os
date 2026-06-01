# Lantern OS Discord Bot v2

Generated: 2026-05-31.

## What's New

Modern slash commands with role-based access gating for a monetized Discord server.

| Feature | v1 | v2 |
|---|---|---|
| Commands | `!dream`, `!note` (prefix) | `/dream`, `/note` (slash) |
| Access control | Single channel allowlist | Role-tier gating |
| Subscriptions | None | Stripe-linked role tiers |
| Notebook | Local JSONL | Local JSONL (same) |
| Voice/Radio | Held behind flags | Held behind flags |

## Quick Start

```powershell
# 1. Set environment variables
$env:DISCORD_BOT_TOKEN = "your_bot_token"
$env:LANTERN_DISCORD_GUILD_ID = "your_guild_id"

# 2. Install dependencies
pip install -r src\discord_lounge_bot\requirements_v2.txt

# 3. Run the bot
python src\discord_lounge_bot\bot_v2.py

# Or use the launcher
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Start-DiscordBotV2.ps1
```

## Commands by Tier

### Public (Free)
- `/status` — Health summary
- `/help` — List commands for your tier
- `/subscribe` — Get Stripe checkout links

### Supporter ($20/month)
- `/dream <text>` — Save dream
- `/note <text>` — Save note
- `/wish <text>` — Save wish
- `/recall [query]` — Search notebook
- `/mirror` — Mirror all facets
- `/wallet` — Check subscription status

### Pilot ($200/month)
- `/converge` — Convergence loop report
- `/rag-status` — RAG intake status
- `/queue` — Agent fleet queue
- `/place <text>` — Save place
- `/character <text>` — Save character
- `/symbol <text>` — Save symbol

### Founder (Operator)
- `/dispatch` — Dispatch agent fleet
- `/controls` — Local controls status
- `/boot-check` — Dual boot readiness
- `/release-gate` — v1.0.0 promotion check

## Role Setup

Create these roles in your Discord server:

| Role | Color | Purpose |
|---|---|---|
| `Supporter` | Teal (#0d9488) | $20/month subscribers |
| `Pilot` | Blue (#2563eb) | $200/month subscribers |
| `Founder` | Amber (#f59e0b) | Operator access |

The bot checks role names case-insensitively.

## Environment Variables

| Variable | Required | Default |
|---|---|---|
| `DISCORD_BOT_TOKEN` | Yes | — |
| `LANTERN_DISCORD_GUILD_ID` | Yes | — |
| `LANTERN_STATUS_URL` | No | `http://127.0.0.1:4177/api/status` |
| `SUBSCRIBER_DATA_PATH` | No | `data/discord/subscribers.json` |

## Safety Boundaries

- No shell/MCP execution from Discord
- No token output in logs
- All notebook entries are private per-user
- Voice join is off by default
- Radio playback requires operator approval

## Deployment

### Docker

```bash
docker build -f ops/Dockerfile-discord-bot-v2 -t lantern-discord-bot-v2 .
docker run -e DISCORD_BOT_TOKEN=$TOKEN -e LANTERN_DISCORD_GUILD_ID=$GUILD_ID lantern-discord-bot-v2
```

### Cloud (Render/Fly.io)

Use `ops/Dockerfile-discord-bot-v2` as the build context.
Set environment variables in the platform dashboard.

## Test Server

Live target: **https://discord.gg/xmsbPjMGm**

Use this server to validate commands before production deployment.

## Migration from v1

v1 bot (`bot.py`) uses prefix commands (`!dream`). v2 (`bot_v2.py`) uses slash commands (`/dream`).
Both can run simultaneously if needed. v1 is kept for backward compatibility.

## License

Same as Lantern OS. Not equity, not investment, not securities.
