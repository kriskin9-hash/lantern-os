# Discord Bot Setup — Phase A Testing

## Problem Fixed
- Bot was trying to join a voice channel that doesn't exist
- Refactored to simpler 4-command set: `/music`, `/art`, `/notes`, `/movies`
- User now joins voice channel first, bot follows

## What You Need to Do NOW

### Step 1: Create Voice Channel in Discord
1. Open your Discord server
2. Go to Voice Channels section
3. Create a new voice channel (can name it anything, e.g., "music-room", "streams", "voice")
4. Test: Click into it to confirm you can join

### Step 2: Start the Bot
```powershell
cd D:\tmp\lantern-os\src\discord_lounge_bot
python bot_v2.py
```

Bot should print:
```
[READY] Logged in as Lantern OS#xxxx at 2026-06-01T...
[SYNC] Synced 27 slash commands globally
```

### Step 3: Test Commands in Discord

**Join voice + play music:**
1. You join a voice channel
2. Type `/music` → bot joins and shows "Now Playing Music"

**See available media:**
- Type `/art` → shows 6 Frank Sinatra songs from Internet Archive
- Type `/movies` → shows same media list

**Add a note:**
- Type `/notes hello world` → saves to your dreamer notebook

### Step 4: Verify in Console

You should see:
```
[COMMAND] user executed /music
[COMMAND] user executed /art
[COMMAND] user executed /notes with content: hello world
```

---

## What Changed

| Old | New |
|-----|-----|
| `/archive-join` | `/music` |
| `/archive-list` | `/art` (or `/movies`) |
| `/archive-play` | Auto-plays first item in `/music` |
| `/archive-next` | Removed (manual /music to restart) |
| `/archive-loop` | Removed (simple player) |
| `/archive-stop` | Bot auto-leaves on disconnect |
| `/archive-leave` | User leaves voice, bot follows |

---

## Success Criteria

- [ ] Bot starts without errors
- [ ] Bot shows 27 commands synced
- [ ] `/music` command joins your voice channel
- [ ] `/art` shows the 6 Sinatra songs
- [ ] `/notes test` saves a note
- [ ] No join/leave loop

---

## If Bot Still Errors

**Check 1:** Is discord.py installed?
```powershell
pip install discord.py
```

**Check 2:** Is DISCORD_BOT_TOKEN set?
```powershell
$env:DISCORD_BOT_TOKEN
```
Should show your bot token. If blank, set it:
```powershell
$env:DISCORD_BOT_TOKEN="your-token-here"
```

**Check 3:** Are you in a voice channel before running `/music`?
The bot won't join empty air. You must be in a voice channel first.

---

## Audio Playback (Future)

Currently, the bot joins and displays what's playing, but doesn't actually stream audio (requires ffmpeg setup). This is fine for Phase A — we're testing Discord integration, not audio yet.

To enable audio playback later:
1. Install ffmpeg: `choco install ffmpeg` (Windows)
2. Uncomment the `cmd_archive_play_internal` function
3. Add `after=` callback to play next track when current ends

---

## Next Steps (After Testing)

Once bot works:
1. Create Linear issues for Phase A
2. Test 2-3 more commands
3. Verify media URLs work (optional for Phase A)

Ready to test?
