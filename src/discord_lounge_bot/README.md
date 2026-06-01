# Discord Lounge Bot

Generated: 2026-05-27.

Purpose: provide a bounded Discord bot for Lantern lounge visibility, safe
health responses, and P0-gated voice/radio access.

## Safety Boundary

- Channel-allowlisted only (`LANTERN_DISCORD_CHANNEL_ID`).
- No shell/MCP command execution from Discord messages.
- No token output in logs.
- Voice join is off unless `LANTERN_DISCORD_ENABLE_VOICE=true`.
- Radio playback is off unless `LANTERN_DISCORD_ENABLE_RADIO=true` and
  `LANTERN_RADIO_URL` points at an operator-approved rights-checked source.
- Commands: `!lantern-status`, `!lantern-voice-check`,
  `!lantern-join-lounge`, `!lantern-leave-lounge`, `!lantern-radio`.

## Required Environment Variables

- `DISCORD_BOT_TOKEN`
- `LANTERN_DISCORD_GUILD_ID`
- `LANTERN_DISCORD_CHANNEL_ID`
- `LANTERN_VOICE_CHANNEL` or `LANTERN_VOICE_CHANNEL_ID`
- optional: `LANTERN_STATUS_URL` (default: `http://127.0.0.1:5001/api/status`)
- optional: `LANTERN_DISCORD_ENABLE_VOICE=true`
- optional: `LANTERN_DISCORD_ENABLE_RADIO=true`
- optional: `LANTERN_RADIO_URL`

## Install

```powershell
pip install -r .\src\discord_lounge_bot\requirements.txt
```

## Health Check

Run this first:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Test-DiscordBotHealth.ps1
```

This script validates:

- required env vars are present;
- token identity check against Discord API succeeds;
- guild and channel IDs are reachable (when provided).
- `discord.py`, `PyNaCl`, and `ffmpeg` are available for voice;
- the configured Lounge voice channel is visible to the bot.

Current P0 rule: do not run `Start-DiscordLoungeBot.ps1`, do not add Lantern to
Lounge, and do not start radio until this health check passes.

## Frank / Rhythm Evidence

The old Frank Sinatra/Rhythm lane lives in the orchestrator repo:

- `C:\Users\alexp\Documents\gm-agent-orchestrator\LANTERN-MASTER-INDEX.md`
- `C:\Users\alexp\Documents\gm-agent-orchestrator\FOUNDRY-PLAN.md`
- `C:\Users\alexp\Documents\gm-agent-orchestrator\lantern-tutorial-frank.html`

Those files describe the tutorial/audio source and offline TTS fallback. This
bot does not auto-stream that material; do not auto-stream any source into
Lounge without an operator rights check. If you want Lounge playback, set
`LANTERN_RADIO_URL` to a rights-checked stream or local file and enable radio
after the P0 health check passes.

## Run

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Start-DiscordLoungeBot.ps1
```

By default, startup runs the health check first. To skip health check:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Start-DiscordLoungeBot.ps1 -NoHealthCheck
```

## Test Server

Live test target: **https://discord.gg/xmsbPjMGm**

Use this server for voice, radio, and notebook command validation. Guild and channel IDs should be configured for this server during testing. See `manifests/TEST-DISCORD-SERVER.md` for the deployment checklist.

## Validation

Acceptance checks:

1. Bot appears online in Discord.
2. Startup status message is posted in the configured channel.
3. `!lantern-status` returns a safe status message.
4. `!lantern-voice-check` shows the configured Lounge gate.
5. `!lantern-join-lounge` joins only after voice is explicitly enabled.
6. Bot ignores other channels.
