# Lantern OS Discord Server — Setup Guide

Generated: 2026-05-31.

## Purpose

Create a monetized Discord server where users buy access tiers and use Lantern OS commands through a modern slash-command bot.

## Server Structure

### Roles

| Role | Price | Color | Permissions |
|---|---|---|---|
| `@everyone` (Public) | Free | Default | Read #welcome, #announcements, #general-chat, #bot-commands |
| `Supporter` | $20/month | Teal (#0d9488) | + #dreamer-well, #support, priority bot commands |
| `Pilot` | $200/month | Blue (#2563eb) | + #pilot-workspace, custom skill commands, 1:1 queue |
| `Founder` | Operator only | Amber (#f59e0b) | + #founder-gate, all commands, admin tools |

### Channels

#### Public (everyone)
- `#welcome` — rules, invite, getting started
- `#announcements` — product updates, convergence reports
- `#general-chat` — open discussion
- `#bot-commands` — all bot slash commands

#### Supporter+
- `#dreamer-well` — share dreams, notes, wishes (bot saves to private notebook)
- `#support` — help desk, weekly digest drops

#### Pilot+
- `#pilot-workspace` — guided sprints, custom integrations
- `#queue-visibility` — agent fleet status, RAG intake

#### Founder only
- `#founder-gate` — local controls, release promotion, secrets (held)

### Voice Channels
- `Lounge` — public voice
- `Pilot Workshop` — Pilot+ voice
- `Founder Council` — Founder only

## Bot Commands

### Public (everyone)
| Command | Description |
|---|---|
| `/status` | Lantern OS health summary |
| `/help` | List available commands for your role |
| `/subscribe` | Get Stripe checkout link for your tier |

### Supporter+
| Command | Description |
|---|---|
| `/dream <text>` | Save a dream to your private notebook |
| `/note <text>` | Save a note |
| `/wish <text>` | Save a wish |
| `/recall [query]` | Search your notebook |
| `/mirror` | Mirror all your facets |
| `/wallet` | Check your subscription and wallet status |

### Pilot+
| Command | Description |
|---|---|
| `/converge` | Run convergence loop report |
| `/rag-status` | Check RAG dollhouse intake |
| `/queue` | View agent fleet queue |
| `/place <text>` | Save a place |
| `/character <text>` | Save a character |
| `/symbol <text>` | Save a symbol |

### Founder
| Command | Description |
|---|---|
| `/dispatch` | Dispatch agent fleet |
| `/controls` | Local controls status |
| `/boot-check` | Dual boot readiness |
| `/release-gate` | v1.0.0 promotion check |

## Stripe Integration

Bot verifies subscription status via:
1. Stripe webhook updates a local `data/discord/subscribers.json` file
2. Bot checks subscriber file before gating commands
3. Role assignment is manual (operator assigns roles after payment clears)

## Environment Variables

```
DISCORD_BOT_TOKEN=<your_bot_token>
LANTERN_DISCORD_GUILD_ID=<new_server_guild_id>
LANTERN_DISCORD_CHANNEL_ID=<bot_commands_channel_id>
STRIPE_SECRET_KEY=sk_test_...
SUBSCRIBER_DATA_PATH=data/discord/subscribers.json
```

## Setup Steps

1. Create new Discord server at https://discord.new
2. Create roles (Supporter, Pilot, Founder) with colors
3. Create channels with role permissions
4. Create bot at https://discord.com/developers/applications
5. Enable "Message Content Intent" and "Server Members Intent"
6. Invite bot with scopes: `bot`, `applications.commands`
7. Set permissions: Send Messages, Embed Links, Connect, Speak, Use Slash Commands
8. Configure env vars
9. Run `pip install discord.py>=2.3.2`
10. Start bot: `python src/discord_lounge_bot/bot_v2.py`

## Safety Boundaries

- No shell/MCP execution from Discord
- No token output in logs
- Voice join is off by default
- Radio playback requires operator approval
- All notebook entries are private per-user
- Subscriber data is local, not in Git

## Test Server

Live target: **https://discord.gg/xmsbPjMGm**

Use this server for command validation before promoting to production.
