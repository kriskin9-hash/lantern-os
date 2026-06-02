# Dream Journal Discord Bot — Setup Guide for New Users

**Status:** ✅ Production Ready  
**Last Updated:** 2026-06-01

---

## Before You Start

This guide assumes you:
- Have Windows 10+, macOS, or Linux
- Can use a terminal/PowerShell
- Have a Discord server you own or can manage
- Can create a Discord bot token

**Time required:** 30–45 minutes

---

## Step 1: Clone the Repository

```powershell
# On Windows
git clone https://github.com/alex-place/lantern-os.git
cd lantern-os
```

```bash
# On macOS/Linux
git clone https://github.com/alex-place/lantern-os.git
cd lantern-os
```

---

## Step 2: Install Python 3.12

### Windows
```powershell
# Via Windows Installer
# Download from https://www.python.org/downloads/
# Run installer, make sure to check "Add Python to PATH"

# Verify
python --version
# Should show: Python 3.12.x
```

### macOS
```bash
# Via Homebrew
brew install python@3.12

# Verify
python3 --version
```

### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install python3.12 python3-pip

# Verify
python3 --version
```

---

## Step 3: Install FFmpeg

### Windows (via WinGet)
```powershell
winget install Gyan.FFmpeg
# Or download from: https://ffmpeg.org/download.html

# Verify
ffmpeg -version
```

### macOS
```bash
brew install ffmpeg

# Verify
ffmpeg -version
```

### Linux (Ubuntu/Debian)
```bash
sudo apt install ffmpeg

# Verify
ffmpeg -version
```

---

## Step 4: Install Python Dependencies

```powershell
# Navigate to the bot directory
cd src/discord_lounge_bot

# Install dependencies
pip install -r requirements_v2.txt

# Verify (should not error)
python -c "import discord; print(discord.__version__)"
```

---

## Step 5: Create a Discord Bot Token

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application"
3. Name it "Lantern OS" (or your preferred name)
4. Go to "Bot" section → "Add Bot"
5. Under TOKEN, click "Copy"
6. Save this token securely (you'll need it in Step 6)

**Important:** Never share your bot token publicly.

---

## Step 6: Get Your Discord Guild ID

1. Enable Developer Mode in Discord (User Settings → Advanced → Developer Mode)
2. Right-click your server name → "Copy Server ID"
3. Save this ID for Step 7

---

## Step 7: Create `.env` File

In the `src/discord_lounge_bot/` directory, create a file called `.env`:

```
DISCORD_BOT_TOKEN=your_bot_token_here
DISCORD_GUILD_ID=your_guild_id_here
LANTERN_STATUS_URL=http://127.0.0.1:4177/api/status
SUBSCRIBER_DATA_PATH=data/discord/subscribers.json
```

Replace:
- `your_bot_token_here` with the token from Step 5
- `your_guild_id_here` with the ID from Step 6

**Note:** The `.env` file should NOT be committed to git. It's in `.gitignore`.

---

## Step 8: Invite Bot to Your Discord Server

1. Go back to Discord Developer Portal
2. Select your "Lantern OS" application
3. Go to "OAuth2" → "URL Generator"
4. Under SCOPES, check:
   - `bot`
5. Under PERMISSIONS, check:
   - `Send Messages`
   - `Use Slash Commands`
   - `Manage Messages`
   - `Connect` (for voice)
   - `Speak` (for voice)
6. Copy the generated URL
7. Paste it in your browser
8. Select your Discord server from the dropdown
9. Authorize

The bot should now appear in your Discord server.

---

## Step 9: Start the Bot

```powershell
# In src/discord_lounge_bot/
python bot_v2.py

# Expected output:
# [INFO] Starting Lantern OS Discord Bot v2...
# [INFO] Slash commands + role gating + notebook integration.
# [READY] Logged in as Lantern OS#xxxx at 2026-06-02T...
# [INFO] Voice player initialized.
```

The bot is now running. It will stay online as long as the terminal is open.

---

## Step 10: Test in Discord

In your Discord server, try these commands:

```
/help              → Shows available commands
/status            → Shows bot + Lantern status
/subscribe         → Shows how to unlock features
/music             → Shows Frank Sinatra collection
/sing "Fly Me to the Moon"  → Plays audio in your voice channel
/nextsong          → Skips to next track
/stop              → Stops playback and disconnects
```

---

## Troubleshooting

### "Bot is offline"
- Check that `python bot_v2.py` is still running
- Check the terminal for error messages
- Verify `DISCORD_BOT_TOKEN` and `DISCORD_GUILD_ID` are correct

### "Command not found"
- Wait 5–10 seconds after bot starts (slash commands take time to sync)
- Refresh Discord (Ctrl+R)
- Check that the bot has "Send Messages" and "Use Slash Commands" permissions

### "Permission denied" errors
- Ensure the bot role has permissions on the channels you're trying to use
- In Discord, go to Server Settings → Roles → "Lantern OS"
- Grant the bot higher permissions if needed

### "FFmpeg not found"
- Ensure FFmpeg is installed (run `ffmpeg -version`)
- Ensure it's in your PATH (restart terminal after install)
- On Windows, use WinGet: `winget install Gyan.FFmpeg`

### Bot crashes on voice commands
- Ensure FFmpeg is installed
- Ensure you're in a voice channel before running `/sing`
- Check terminal for detailed error messages

---

## Making the Bot Persistent (Optional)

To keep the bot running even after you close the terminal:

### Windows (using Task Scheduler)
```powershell
# Create a batch file: start-bot.bat
@echo off
cd D:\tmp\lantern-os\src\discord_lounge_bot
python bot_v2.py
pause
```

Then schedule it to run on startup using Task Scheduler.

### macOS/Linux (using systemd)
Create `/etc/systemd/system/lantern-bot.service`:
```ini
[Unit]
Description=Lantern OS Discord Bot
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/lantern-os/src/discord_lounge_bot
ExecStart=/usr/bin/python3 bot_v2.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable lantern-bot
sudo systemctl start lantern-bot
```

---

## Next Steps

Once the bot is working:

1. **Create Discord roles:** Supporter, Pilot, Founder
2. **Create Discord channels:** #dreamer-well, #pilot-workspace, etc.
3. **Set up Patreon:** Create tiers and connect to Discord via OAuth
4. **Test command gating:** Verify different roles see different commands
5. **Invite test users:** Start a soft launch with 10 trusted friends

---

## Support

- **Docs:** See BOT-SETUP-GUIDE.md for detailed command reference
- **Source:** https://github.com/alex-place/lantern-os
- **Issues:** Report bugs in the repo's issues section

---

## Status

✅ **Ready for production use**

This bot has been tested on Windows 10+ and is actively running in production.
