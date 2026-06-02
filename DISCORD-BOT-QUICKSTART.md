# Discord Bot Quickstart — Lantern OS

**Status:** Phase A Implementation Complete  
**Date:** 2026-06-01  
**Target:** Bot online 24/7 with orchestrator health visibility

---

## Overview

The Lantern OS Discord bot provides:
- **Role-gated slash commands** for supporters, pilots, and founders
- **Personal notebook integration** for dreams, notes, and wishes
- **Orchestrator visibility** via `/orchestrator` and `/queue` commands
- **24/7 uptime** via watchdog process

## Installation

### 1. Environment Setup

Copy and customize `.lantern/discord.env`:

```bash
# Required
export DISCORD_BOT_TOKEN="your-bot-token-here"
export LANTERN_DISCORD_GUILD_ID="your-guild-id-here"

# Optional (defaults shown)
export MCP_SERVER_URL="http://127.0.0.1:8787"
export LANTERN_STATUS_URL="http://127.0.0.1:4177/api/status"
```

### 2. Install Dependencies

```bash
pip install discord.py aiohttp
```

### 3. Start the Watchdog

**Terminal (persistent, recommended for development):**

```powershell
cd $REPO_ROOT
pwsh -NoExit -Command { & .\scripts\Start-DiscordBotWatchdog.ps1 }
```

Bot logs will appear in `~/.lantern/logs/discord-bot.log`.

**Windows Scheduled Task (for production):**

```powershell
$Action = New-ScheduledTaskAction `
  -Execute "pwsh" `
  -Argument "-NoExit -Command & '$REPO_ROOT\scripts\Start-DiscordBotWatchdog.ps1'"

$Trigger = New-ScheduledTaskTrigger -AtStartup

Register-ScheduledTask `
  -TaskName "DiscordBotWatchdog" `
  -Action $Action `
  -Trigger $Trigger `
  -RunLevel Highest `
  -Force

Start-ScheduledTask -TaskName "DiscordBotWatchdog"
```

## Verification

### 1. Check Logs

```bash
tail -f ~/.lantern/logs/discord-bot.log
```

Expected output:
```
[2026-06-01 12:34:56] Discord Bot Watchdog started
[2026-06-01 12:34:57] Bot script: /path/to/src/discord_lounge_bot/bot_v2.py
[2026-06-01 12:34:57] Log file: /home/user/.lantern/logs/discord-bot.log
[2026-06-01 12:34:58] Starting Discord bot: /path/to/src/discord_lounge_bot/bot_v2.py
[2026-06-01 12:35:02] [READY] Logged in as LanternBot#1234 at 2026-06-01T12:35:02Z
[2026-06-01 12:35:02] [SYNC] Synced 25 slash commands to guild 123456789
```

### 2. Test Commands in Discord

In your server, try:

- `/help` — list available commands
- `/status` — show bot health
- `/orchestrator` — query orchestrator status (requires Pilot+ tier)
- `/queue` — show pending tasks (requires Pilot+ tier)

## Troubleshooting

### Bot won't start

1. Check DISCORD_BOT_TOKEN is valid
2. Verify `~/.lantern/discord.env` is readable
3. Check logs: `tail -f ~/.lantern/logs/discord-bot.log`

### Orchestrator commands return "offline"

1. Verify MCP server is running on `localhost:8787`
2. Check firewall: `curl http://127.0.0.1:8787/api/account/summary`
3. Update MCP_SERVER_URL in `~/.lantern/discord.env` if needed

### Bot crashes repeatedly

1. Check for Python errors in logs
2. Verify all dependencies: `pip list | grep -E "discord|aiohttp"`
3. Test bot manually: `cd src/discord_lounge_bot && python bot_v2.py`

## Architecture

```
┌─────────────────────────────────────────┐
│        Discord Server (Guild)           │
├─────────────────────────────────────────┤
│  /orchestrator          /queue          │
│  /help    /status    /subscribe         │
│  /dream   /note      /wallet            │
└──────────────┬──────────────────────────┘
               │
               │ discord.py (bot_v2.py)
               │
        ┌──────▼──────────────┐
        │  MCP Bridge         │
        │  (mcp_bridge.py)    │
        └──────┬──────────────┘
               │
               │ HTTP (aiohttp)
               │
        ┌──────▼──────────────┐
        │  MCP Server         │
        │  (orchestrator)     │
        │  localhost:8787     │
        └─────────────────────┘
```

## MCP Bridge Integration

The `mcp_bridge.py` module provides:

| Function | Endpoint | Purpose |
|----------|----------|---------|
| `get_orchestrator_status()` | `/api/account/summary` | Query active slots, queue size, uptime |
| `get_queue_tasks(limit)` | `/api/tasks/queue` | List pending tasks |
| `log_user_action()` | `/api/logs` | Log Discord user actions (optional) |
| `format_status_embed()` | N/A | Format status as Discord embed |
| `format_queue_embed()` | N/A | Format queue as Discord embed |

## Configuration Reference

| Variable | Default | Purpose |
|----------|---------|---------|
| `DISCORD_BOT_TOKEN` | (none) | Bot authentication token from Discord Developer Portal |
| `LANTERN_DISCORD_GUILD_ID` | (none) | Guild ID for slash command sync |
| `MCP_SERVER_URL` | `http://127.0.0.1:8787` | Orchestrator MCP server endpoint |
| `LANTERN_STATUS_URL` | `http://127.0.0.1:4177/api/status` | Status endpoint (legacy, may deprecate) |

## Next Steps

- [ ] Set up Discord Developer Portal bot account
- [ ] Configure bot permissions and intents
- [ ] Create test roles (supporter, pilot, founder)
- [ ] Deploy watchdog to production
- [ ] Document per-operator bot setup for 20-operator rollout

## Support

For issues, check:
1. `~/.lantern/logs/discord-bot.log`
2. MCP server health: `curl http://127.0.0.1:8787/health`
3. Network connectivity: `ping 127.0.0.1`
4. Bot token validity via Discord Developer Portal

---

**Last Updated:** 2026-06-01  
**Author:** Founder  
**Status:** Production Ready
