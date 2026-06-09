# Lantern OS / Dream Journal — Install Guide

> **OS:** Windows 10/11  
> **Last updated:** 2026-06-09  
> **Primary server:** Node.js 18+  

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start (One-Click Installer)](#quick-start-one-click-installer)
3. [Manual Install](#manual-install)
4. [Environment Variables](#environment-variables)
5. [Starting the App](#starting-the-app)
6. [Discord Bot (Optional)](#discord-bot-optional)
7. [Verification](#verification)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

| Requirement | Minimum Version | Notes |
|---|---|---|
| **Windows** | 10 (build 19041+) or 11 | `winver` |
| **Git** | 2.40+ | [git-scm.com](https://git-scm.com/download/win) |
| **Node.js** | 18+ | [nodejs.org](https://nodejs.org) — **required** for the web server |
| **Python** | 3.10+ | [python.org](https://www.python.org/downloads/) — only needed for Discord bot / MCP server |
| **ffmpeg** | Any recent | `winget install Gyan.FFmpeg` — only needed for Discord voice / lounge music |

**Check what you have:**

```powershell
node --version    # must be v18+
python --version  # 3.10+ if running the Discord bot
git --version
ffmpeg -version   # optional
```

---

## Quick Start (One-Click Installer)

The fastest way to get Dream Journal running.

### 1. Open PowerShell

```powershell
# Run from the web:
irm https://raw.githubusercontent.com/alex-place/lantern-os/master/scripts/install-dream-journal.ps1 | iex
```

**What the script does:**

1. Validates prerequisites (Git, Node.js 18+, Python optional, ffmpeg optional).
2. Clones `https://github.com/alex-place/lantern-os.git` to `~\lantern-os` (or updates an existing clone).
3. Runs `npm install` in `apps/lantern-garage`.
4. Runs `pip install -r requirements.txt` (if Python is present).
5. Copies `.env.example` → `.env` if no `.env` exists.
6. Creates a desktop shortcut named **Dream Journal**.
7. Optionally launches the server and opens your browser.

**Estimated time:** 2–5 minutes.

> **Safe to re-run:** The installer is idempotent. Running it again updates the repo and dependencies without touching your data or `.env`.

### 2. Add at least one API key

Open `~\lantern-os\.env` in any text editor and add your key(s):

```ini
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=...
OPENAI_API_KEY=sk-...
```

You only need **one** key to start chatting. Gemini has a generous free tier.

### 3. Start the server

Double-click the **Dream Journal** shortcut on your Desktop, or run:

```powershell
powershell -File "$env:USERPROFILE\lantern-os\scripts\Start-DreamJournal.ps1"
```

Open [http://127.0.0.1:4177](http://127.0.0.1:4177).

---

## Manual Install

### Step 1 — Clone the repository

```powershell
cd $env:USERPROFILE
git clone https://github.com/alex-place/lantern-os.git
cd lantern-os
```

### Step 2 — Install Node.js dependencies

```powershell
npm install --prefix apps/lantern-garage
```

### Step 3 — Install Python dependencies (optional)

Only needed if you want the Discord bot or MCP server:

```powershell
python -m pip install -r requirements.txt
```

### Step 4 — Set up environment variables

```powershell
copy .env.example .env
# Edit .env and add your API keys
notepad .env
```

### Step 5 — Start the server

```powershell
node apps/lantern-garage/server.js
```

---

## Environment Variables

Copy `.env.example` to `.env` at the repo root. Key variables:

| Variable | Required | Purpose |
|---|---|---|
| `ANTHROPIC_API_KEY` | One of these | Claude — high quality, paid |
| `GEMINI_API_KEY` | One of these | Gemini — free tier available |
| `OPENAI_API_KEY` | One of these | GPT-4o-mini — cost-efficient |
| `DISCORD_BOT_TOKEN` | Discord only | Bot token from [discord.com/developers](https://discord.com/developers) |
| `LANTERN_DISCORD_GUILD_ID` | Discord only | Right-click your server → Copy Server ID |

> **Security:** `.env` is git-ignored and never committed. Keep it outside the repo if you use cloud sync.

---

## Starting the App

### Web server (required)

```powershell
node apps/lantern-garage/server.js
```

Or via npm:

```powershell
npm start --prefix apps/lantern-garage
```

Open [http://127.0.0.1:4177](http://127.0.0.1:4177) — the Dream Journal chat UI.

**What starts automatically:**
- Dream Journal chat UI
- REST API (`/api/dream/*`, `/api/settings/providers`)
- SSE streaming endpoint
- Discord bot (if `DISCORD_BOT_TOKEN` and `LANTERN_DISCORD_GUILD_ID` are in `.env`)

### MCP server (optional)

```powershell
python src/mcp_server/server.py
```

Port: `8771`

---

## Discord Bot (Optional)

The Discord bot (Lantern lounge, voice music, dream journal integration) starts **automatically** when you run the Node.js server — no separate terminal needed.

**Setup:**

1. Go to [discord.com/developers](https://discord.com/developers/applications) → New Application → Bot.
2. Copy the bot token.
3. Add to `.env`:
   ```ini
   DISCORD_BOT_TOKEN=your_token_here
   LANTERN_DISCORD_GUILD_ID=your_server_id_here
   ```
4. Invite the bot to your server (replace `YOUR_CLIENT_ID`):
   ```
   https://discord.com/oauth2/authorize?client_id=YOUR_CLIENT_ID&permissions=8&scope=bot%20applications.commands
   ```
5. Start the server normally — bot starts with it.

**For voice / lounge music**, install ffmpeg first:

```powershell
winget install Gyan.FFmpeg
```

Then restart PowerShell so `ffmpeg` is on your PATH.

---

## Verification

After starting the server:

```powershell
# Health check
Invoke-RestMethod -Uri "http://127.0.0.1:4177/api/health"
# Expected: { "ok": true, "service": "lantern-garage", ... }
```

In your browser: open [http://127.0.0.1:4177](http://127.0.0.1:4177) and send a message in the Dream Journal chat.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `irm` blocked by execution policy | `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser` then re-run |
| `node` not found | Install Node.js 18+ from [nodejs.org](https://nodejs.org), restart terminal |
| Port 4177 already in use | `netstat -ano \| findstr :4177` to find the PID, then stop it |
| No AI responses | Add at least one key to `.env` and restart the server |
| Discord bot not connecting | Check `DISCORD_BOT_TOKEN` and `LANTERN_DISCORD_GUILD_ID` in `.env` |
| Bot can't join voice / no audio | Install ffmpeg: `winget install Gyan.FFmpeg`, then restart terminal |
| `npm install` fails | Check Node.js version (`node --version`); update if below 18 |
| Python package errors | Use a virtual environment: `python -m venv .venv && .venv\Scripts\Activate.ps1` |

---

## File Reference

| File | Purpose |
|---|---|
| `scripts/install-dream-journal.ps1` | One-click Windows installer |
| `scripts/Start-DreamJournal.ps1` | Desktop shortcut target — starts Node.js server |
| `apps/lantern-garage/server.js` | Primary web server (Node.js, port 4177) |
| `src/discord_lounge_bot/bot_v2.py` | Discord bot (auto-started by server.js) |
| `src/mcp_server/server.py` | MCP tool server (port 8771) |
| `.env.example` | Environment variable template |
| `QUICKSTART.md` | Developer quick-start and full-stack guide |

---

**Happy journaling. Light the lantern.**
