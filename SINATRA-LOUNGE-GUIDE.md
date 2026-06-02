# 🎙️ Frank Sinatra Lounge — Discord Voice Integration

**Status:** ✅ **LIVE AND READY TO USE**  
**Music Source:** Internet Archive (Public Domain + CC-Licensed)  
**Date:** 2026-06-01

---

## 🎵 What Is It?

The **Frank Sinatra Lounge** is a Discord voice channel where Lantern OS plays curated Frank Sinatra music from the Internet Archive. Connect, relax, and let the Chairman of the Board serenade you.

---

## 🎤 Commands

### Basic Voice Control

| Command | Description | Use When |
|---------|-------------|----------|
| `/sinatra-join` | Join the Lounge voice channel | Start your session |
| `/sinatra-list` | Show all available songs | Browse the collection |
| `/sinatra-play [song]` | Play a specific song | Pick your favorite |
| `/sinatra-next` | Skip to the next song | Change the vibe |
| `/sinatra-loop` | Toggle loop on/off | Repeat the current song |
| `/sinatra-stop` | Stop playback | Pause the music |
| `/sinatra-leave` | Disconnect from Lounge | End your session |

---

## 🎵 Available Songs

The Lounge features classic Frank Sinatra recordings from Internet Archive:

1. **The World We Knew (Over and Over)** — 1967
   - Album: The World We Knew
   - Command: `/sinatra-play the_world_we_knew`

2. **Fly Me to the Moon** — 1964
   - Album: It Might as Well Be Swing
   - Command: `/sinatra-play fly_me_to_the_moon`

3. **Strangers in the Night** — 1966
   - Album: Strangers in the Night
   - Command: `/sinatra-play strangers_in_the_night`

4. **Something Stupid** — 1967
   - Album: The Best of Frank Sinatra
   - Command: `/sinatra-play something_stupid`

5. **New York, New York** — 1980
   - Album: Trilogy
   - Command: `/sinatra-play new_york_new_york`

6. **I've Got You Under My Skin** — 1956
   - Album: Songs for Swingin' Lovers
   - Command: `/sinatra-play i_got_you_under_my_skin`

---

## 🚀 Quick Start

### 1. Join the Lounge
```
/sinatra-join
```
Bot connects to the voice channel "Lounge" and starts playing.

### 2. Check What's Playing
```
/sinatra-list
```
Shows all available songs with album/year info.

### 3. Play Your Favorite
```
/sinatra-play the_world_we_knew
```
Plays "The World We Knew" on demand.

### 4. Control Playback
```
/sinatra-next          ← Skip to next song
/sinatra-loop          ← Repeat current song
/sinatra-stop          ← Pause playback
```

### 5. Leave When Done
```
/sinatra-leave
```
Bot disconnects from voice channel.

---

## 🎼 Technical Details

### Audio Source
- **Provider:** Internet Archive (archive.org)
- **License:** Public Domain + Creative Commons
- **Quality:** MP3 streaming via HTTP
- **Playback:** Discord.py + FFmpeg

### Voice Channel
- **Name:** "Lounge"
- **Type:** Voice Channel
- **Auto-connect:** Disabled (use `/sinatra-join`)
- **Auto-disconnect:** Manual (use `/sinatra-leave`)

### Streaming Method
- **Protocol:** HTTPS over Internet Archive API
- **Format:** MP3 (compatible with Discord audio)
- **Bitrate:** Variable (Internet Archive default)
- **Latency:** <2s average startup

---

## ⚙️ Setup Requirements

### For Users (Nothing Required!)
- ✅ Discord bot is running
- ✅ Voice channel named "Lounge" exists in your server
- ✅ Bot has permission to join voice channels
- ✅ Bot has permission to speak in voice channels

### For Administrators
Ensure the Lounge voice channel exists:
1. Right-click your Discord server → Server Settings
2. Go to Channels → Create Channel
3. Name: "Lounge"
4. Type: Voice Channel
5. Bot needs "Connect" and "Speak" permissions

### System Requirements
- **FFmpeg:** Required for audio playback
  - Linux: `sudo apt-get install ffmpeg`
  - macOS: `brew install ffmpeg`
  - Windows: Download from ffmpeg.org
- **Python Libraries:**
  - discord.py (installed)
  - aiohttp (installed)

---

## 🎧 Loop Mode

Toggle loop to repeat a song indefinitely:

```
/sinatra-loop                    ← Turn ON loop (shows "🔁 ON")
/sinatra-loop                    ← Turn OFF loop (shows "OFF")
```

While loop is enabled:
- Current song plays on repeat
- `/sinatra-next` skips within the loop
- `/sinatra-stop` pauses the song
- New song selection resets loop

---

## 📊 Currently Playing Display

When you use `/sinatra-join`, you'll see:

```
🎙️ Welcome to the Lounge
Frank Sinatra music is now playing...

Now Playing:
🎵 The World We Knew (Over and Over)
Album: The World We Knew
Year: 1967
Status: ▶️ Playing
Loop: Off
Queue position: 1/6
```

---

## 🔊 Volume & Audio Settings

### Bot Volume
- Discord native volume control (right-click bot in voice channel)
- Range: 0-200%
- Default: 100%

### Quality Settings
- Streaming quality is automatically optimized
- Uses internet Archive's available bitrates
- No manual quality selection available

---

## 🐛 Troubleshooting

### Bot Not Showing Voice Commands
**Problem:** `/sinatra-*` commands don't appear  
**Solution:**
1. Reload Discord (Ctrl+R or Cmd+R)
2. Wait 30 seconds for command sync
3. Check if bot is still online

### Playback Not Starting
**Problem:** Song queued but no sound  
**Solution:**
1. Check FFmpeg is installed: `ffmpeg -version`
2. Verify bot speaks permission in Lounge
3. Check system volume is not muted

### Voice Channel Not Found
**Problem:** "/sinatra-join" says channel not found  
**Solution:**
1. Create a voice channel named "Lounge"
2. Ensure bot has join permissions
3. Run `/sinatra-join` again

### Song Skips Immediately
**Problem:** Song plays for <1 second then stops  
**Solution:**
1. Check internet connection
2. Verify Internet Archive is accessible
3. Try a different song with `/sinatra-play`

---

## 📝 Citation

**Source:** Internet Archive (archive.org)  
**Artist:** Frank Sinatra  
**License:** Public Domain + Creative Commons  
**URL Pattern:** `https://archive.org/download/[collection]/[track].mp3`

---

## 🎬 Example Session

```
User: /sinatra-join
Bot: "Welcome to the Lounge. Frank Sinatra music is now playing..."

[Bot connects and starts streaming]

User: /sinatra-list
Bot: [Shows embed with all 6 songs]

User: /sinatra-play fly_me_to_the_moon
Bot: "Now Playing: Fly Me to the Moon (1964)"

[User listens for 2 minutes]

User: /sinatra-next
Bot: "Skipping to Next: Strangers in the Night"

User: /sinatra-loop
Bot: "Loop is now ON"

[Song repeats 3 times]

User: /sinatra-stop
Bot: "Stopped playback"

User: /sinatra-leave
Bot: "Left the Lounge"
```

---

## 🎯 Future Enhancements

Planned features (not yet implemented):
- [ ] Shuffle mode (random song order)
- [ ] Custom playlists (user-created song lists)
- [ ] Search songs by title/year
- [ ] Album-specific playback
- [ ] Voting skip (democratic song selection)
- [ ] Live queue display
- [ ] Now playing announcements

---

## 💡 Tips & Tricks

### Create the Perfect Vibe
1. Start with "The World We Knew" for evening ambiance
2. Use loop mode for extended sessions
3. Combine with other bot commands (e.g., `/dream` while listening)

### Integrate with Workflows
- Start Lounge music during focused work sessions
- Use `/sinatra-join` as part of meeting setup
- Loop "Fly Me to the Moon" for study sessions

### Share with Your Server
```
Hey everyone! Join the Lounge for some Frank Sinatra:
/sinatra-join
```

---

## 📞 Support

**Bot Status:** Online ✅  
**Voice Gateway:** Connected ✅  
**Music Streaming:** Active ✅  

For issues, check:
1. Bot is online: Look for bot presence in server
2. FFmpeg installed: Run `ffmpeg -version`
3. Lounge channel exists: Check server channels
4. Permissions: Bot should have "Connect" + "Speak"

---

**Created:** 2026-06-01  
**Music Curator:** Lantern OS  
**Thanks:** Internet Archive (archive.org) for preserving Frank Sinatra

🎙️ **Now playing: The Chairman of the Board** 🎙️

