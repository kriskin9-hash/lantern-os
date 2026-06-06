# Lantern OS — Script Inventory

One-stop reference for every runnable script in the repo. Skip the archaeology next time.

**Rule of thumb:** Scripts under `scripts/` are operational. Scripts under `archive/` are frozen history. Scripts under `lantern-discord/` are deployment wrappers.

---

## Core Startup (Single Command)

| Script | Purpose | How to run |
|--------|---------|-----------|
| `npm start` (in `apps/lantern-garage/`) | Starts the web server (port 4177) **and** spawns the Discord bot automatically if `DISCORD_BOT_TOKEN` + `LANTERN_DISCORD_GUILD_ID` are set in `.env.local` | `cd apps/lantern-garage && npm start` |
| `apps/lantern-garage/server.js` | Node HTTP server with modular routes. Loads `.env.local` / `.env` from repo root. | `node apps/lantern-garage/server.js` |
| `apps/lantern-garage/cloud-server.js` | Thin wrapper for Railway/Render deploys. | `node apps/lantern-garage/cloud-server.js` |

---

## Discord Bot

See repository scripts and launcher wrappers for current Discord bot operations.