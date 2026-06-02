# Discord Lounge Bot Setup Guide

**Status:** Ready for authentication and deployment  
**Last Updated:** 2026-05-31  
**Test Server:** https://discord.gg/xmsbPjMGm

---

## Quick Start (Choose One)

### Option 1: Interactive Setup (Recommended)
```powershell
# Full interactive setup with token input and guild/channel discovery
cd D:\tmp\lantern-discord
.\Setup-DiscordBotAuth.ps1
```

**What it does:**
1. Prompts for Discord bot token (secure input)
2. Validates token against Discord API
3. Discovers all guilds and channels bot has access to
4. Generates `.env` file with full configuration
5. Shows next steps for deployment

**Output:** `.env` file in current directory with all required variables

---

### Option 2: CLI Token Validation (Quick Check)
```powershell
# Just validate a token (no env file generation)
.\Test-DiscordToken.ps1 -Token "YOUR_BOT_TOKEN_HERE"

# Also check guild and channel access
.\Test-DiscordToken.ps1 -Token "YOUR_BOT_TOKEN_HERE" `
  -GuildId "123456789" `
  -ChannelId "987654321"

# Test sending a message
.\Test-DiscordToken.ps1 -Token "YOUR_BOT_TOKEN_HERE" `
  -GuildId "123456789" `
  -ChannelId "987654321"
```

---

### Option 3: Bash/curl CLI (For SSH/Linux)
```bash
# Make script executable
chmod +x ./test-discord-token.sh

# Validate token
./test-discord-token.sh "YOUR_BOT_TOKEN_HERE"

# Full validation
./test-discord-token.sh "YOUR_BOT_TOKEN_HERE" "123456789" "987654321"
```

---

## How to Get a Discord Bot Token

### Step 1: Create Application in Discord Developer Portal

1. Go to: https://discord.com/developers/applications
2. Click **"New Application"** 
3. Name it: **"Lantern Lounge"**
4. Click **"Create"**

### Step 2: Create Bot User

1. Go to **"Bot"** section in left sidebar
2. Click **"Add Bot"**
3. Under **"TOKEN"** section, click **"Copy"** to copy your bot token
   - ⚠️ **NEVER share this token publicly!**
   - Treat it like a password

### Step 3: Configure Bot Permissions (OAuth2)

1. Go to **"OAuth2"** → **"URL Generator"**
2. Under **"SCOPES"**, select:
   - ✅ `bot`
3. Under **"PERMISSIONS"**, select:
   - ✅ Send Messages
   - ✅ Read Messages/View Channels
   - ✅ Connect (for voice)
   - ✅ Speak (for voice/radio)
   - ✅ Embed Links
   - ✅ Attach Files
   - ✅ Read Message History

4. Copy the generated **authorization URL**
5. Paste it in your browser to add the bot to your Discord server

### Step 4: Run Setup Script

Paste your bot token into the setup script:

```powershell
.\Setup-DiscordBotAuth.ps1
```

When prompted, paste the token you copied from Step 2.

---

## Environment Variables Reference

The setup script generates a `.env` file with these variables:

```env
# Required: Your Discord bot token (from Developer Portal)
DISCORD_BOT_TOKEN=<your_bot_token_here>

# Guild (Server) Configuration
LANTERN_DISCORD_GUILD_ID=<guild_id_from_your_server>
LANTERN_DISCORD_GUILD_NAME=<name_of_guild>

# Bot Command Channel (where bot posts status and listens for commands)
LANTERN_DISCORD_CHANNEL_ID=<text_channel_id>
LANTERN_DISCORD_CHANNEL_NAME=<text_channel_name>

# Voice Lounge Channel (where bot can join voice)
LANTERN_VOICE_CHANNEL_ID=<voice_channel_id>
LANTERN_VOICE_CHANNEL_NAME=<voice_channel_name>

# Optional: Health Check Endpoint
LANTERN_STATUS_URL=http://127.0.0.1:5001/api/status

# Optional: Enable Voice Support (default: false)
LANTERN_DISCORD_ENABLE_VOICE=false

# Optional: Enable Radio Playback (default: false)
LANTERN_DISCORD_ENABLE_RADIO=false
LANTERN_RADIO_URL=
```

---

## Workflow: From Token to Running Bot

### Step 1: Setup & Configuration
```powershell
# Run interactive setup
.\Setup-DiscordBotAuth.ps1

# This creates .env file with all values
```

### Step 2: Load Environment Variables
```powershell
# Load .env into current session
Get-Content .env | ForEach-Object {
    if ($_ -match '^\s*([A-Za-z_][A-Za-z0-9_]*)=(.*)$') {
        $name = $matches[1]
        $value = $matches[2]
        Set-Item -Path "env:$name" -Value "$value"
    }
}

# Verify variables are loaded
$env:DISCORD_BOT_TOKEN  # Should not be empty
$env:LANTERN_DISCORD_GUILD_ID
```

### Step 3: Run Health Check
```powershell
# Validate bot can connect and access channels
.\scripts\Test-DiscordBotHealth.ps1

# Expected output:
# ✓ Bot token valid
# ✓ Guild accessible
# ✓ Text channel accessible
# ✓ Voice channel accessible
# ✓ Ready to start bot
```

### Step 4: Start Bot
```powershell
# Once health check passes, start the bot
.\scripts\Start-DiscordLoungeBot.ps1

# Bot should appear online in Discord
# Bot should post startup message to configured channel
```

### Step 5: Test Bot Commands
In your Discord server's bot channel:
```
!lantern-status          # Check bot health
!lantern-voice-check     # Check voice lounge
!lantern-join-lounge     # Join voice channel (if enabled)
!lantern-leave-lounge    # Leave voice channel
!lantern-radio           # Play radio (if enabled)
```

---

## Troubleshooting

### Token Validation Fails
**Error:** "401 Unauthorized"
- ✓ Check token is copied completely (no extra spaces)
- ✓ Token must be from **Bot** section, not OAuth2 Client Secret
- ✓ Token may have expired — regenerate in Developer Portal

### Guild Not Found
**Error:** "Guild not accessible"
- ✓ Bot must be added to the Discord server first
- ✓ Use the authorization URL from OAuth2 URL Generator
- ✓ Verify correct Guild ID is being used

### Channel Not Accessible
**Error:** "Channel not accessible"
- ✓ Bot role must have permission to view channel
- ✓ Check channel permissions in Discord (Settings → Permissions)
- ✓ Channel type must match (text for commands, voice for lounge)

### Cannot Send Messages
**Error:** "Cannot send message"
- ✓ Bot role needs "Send Messages" permission
- ✓ Channel must allow bot messages (check role permissions)
- ✓ Bot must have "View Channel" permission

### Environment Variables Not Loading
```powershell
# Check if variables are set
Get-ChildItem env: | grep DISCORD

# Manually set if needed
$env:DISCORD_BOT_TOKEN = "MTAx..."
$env:LANTERN_DISCORD_GUILD_ID = "123456789"
```

---

## Security Best Practices

### ✅ DO

- ✅ Keep bot token in `.env` file (not in version control)
- ✅ Use `.gitignore` to exclude `.env` files
- ✅ Regenerate token if accidentally exposed
- ✅ Restrict bot to specific channels
- ✅ Use least-privilege permissions (only what bot needs)

### ❌ DON'T

- ❌ Commit `.env` file to git
- ❌ Share token in Discord/Slack/email
- ❌ Log token in console output
- ❌ Use admin permissions unless required
- ❌ Enable features (voice, radio) unless configured

---

## Test Server Details

**Discord Server:** https://discord.gg/xmsbPjMGm  
**Purpose:** Bot testing and validation  
**Channels:** #general, #voice-lounge, #bot-test  

To get Guild ID and Channel IDs from test server:
1. Enable Developer Mode in Discord (User Settings → Advanced → Developer Mode)
2. Right-click on server name → "Copy Server ID" (Guild ID)
3. Right-click on channel name → "Copy Channel ID" (Channel ID)
4. Use these IDs in setup script

---

## Next Steps After Setup

1. ✅ Run setup script (`Setup-DiscordBotAuth.ps1`)
2. ✅ Validate token (`Test-DiscordToken.ps1`)
3. ✅ Run health check (`Test-DiscordBotHealth.ps1`)
4. ✅ Start bot (`Start-DiscordLoungeBot.ps1`)
5. 🔄 Test commands in Discord channel
6. 🔄 Enable voice/radio if desired
7. 📝 Configure for production Lounge

---

## Files Reference

| Script | Purpose |
|--------|---------|
| `Setup-DiscordBotAuth.ps1` | Interactive token input and config generation |
| `Test-DiscordToken.ps1` | Quick CLI token validation |
| `test-discord-token.sh` | Bash/curl version (no PowerShell) |
| `.env` | Generated config file (keep secure!) |
| `scripts/Test-DiscordBotHealth.ps1` | Pre-deployment health check |
| `scripts/Start-DiscordLoungeBot.ps1` | Start the bot |

---

**Status:** Ready for production deployment  
**Last Tested:** 2026-05-31  
**Documentation:** https://github.com/alex-place/lantern-os/blob/master/src/discord_lounge_bot/README.md
