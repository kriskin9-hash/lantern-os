# Test Discord Server

**Invite:** https://discord.gg/xmsbPjMGm  
**Registered:** 2026-05-31T06:19:00Z  
**Purpose:** Live test target for Lantern Discord lounge bot — voice, radio, notebook commands, and convergence loop feedback.

## Bot Deployment Checklist

- [ ] Bot application created in Discord Developer Portal
- [ ] Token stored in `.env` (not committed)
- [ ] Guild ID configured (`LANTERN_DISCORD_GUILD_ID`)
- [ ] Channel ID configured (`LANTERN_DISCORD_CHANNEL_ID`)
- [ ] Voice channel configured (`LANTERN_VOICE_CHANNEL` or `LANTERN_VOICE_CHANNEL_ID`)
- [ ] Health check passes (`Test-DiscordBotHealth.ps1`)
- [ ] Notebook commands verified (`!dream`, `!note`, `!recall`)
- [ ] Voice join verified (`!lantern-join-lounge`)
- [ ] Radio playback verified (`!lantern-radio`)
- [ ] Loop playback verified (`!lantern-loop`)

## Boundaries

- Do not auto-stream copyrighted material.
- Only rights-checked sources or local files for radio.
- No shell/MCP execution from Discord messages.
- Bot is channel-allowlisted — ignores other channels.

## Next Actions

1. Run `Test-DiscordBotHealth.ps1` against this server.
2. Invite the bot using OAuth2 URL from Developer Portal.
3. Test voice join and playback.
4. Record results in `data/automation/` receipt.
