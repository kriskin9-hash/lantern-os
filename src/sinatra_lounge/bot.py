# -*- coding: utf-8 -*-
"""
Lantern Lounge Bot — Discord voice music player
Streams from Internet Archive: Frank Sinatra radio recordings + binaural beats.

Modes
-----
  sinatra  — 1940s-50s Frank Sinatra radio broadcast transcription discs
  dreams   — delta/theta binaural beats for sleep and dream induction
  focus    — alpha/beta binaural beats for concentration and flow

Commands (prefix ! or slash /)
-------------------------------
  !lounge [channel]  — join voice and start Sinatra
  !dreams            — switch to dream binaural beats
  !focus             — switch to focus binaural beats
  !skip   / !s       — skip current track
  !stop              — stop playback (stay in channel)
  !leave  / !bye     — stop and disconnect
  !np                — now playing
  !volume <0-100>    — set volume
  !queue             — show upcoming tracks
  !mode              — show current mode
  !catalog           — list loaded tracks by mode
  !shuffle           — re-shuffle the queue

Requirements
------------
  pip install "discord.py[voice]" PyNaCl
  ffmpeg on PATH:
    Windows: winget install Gyan.FFmpeg
    macOS:   brew install ffmpeg

Environment
-----------
  LOUNGE_BOT_TOKEN        — dedicated bot token (preferred)
  DISCORD_BOT_TOKEN       — fallback to main bot token
  LANTERN_DISCORD_GUILD_ID — guild ID for slash command sync
  LOUNGE_VOICE_CHANNEL    — default voice channel name (default: "Sinatra Lounge")
"""

from __future__ import annotations

import asyncio
import json
import os
import random
import sys
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

try:
    import discord
    from discord import app_commands
except ImportError:
    print("[FATAL] discord.py not installed. Run: pip install \"discord.py[voice]\" PyNaCl")
    sys.exit(1)

# ── Env loading ────────────────────────────────────────────────────────────────

_REPO_ROOT = Path(__file__).resolve().parents[2]
for _f in [".env", ".env.local"]:
    _p = _REPO_ROOT / _f
    if _p.exists():
        for _line in _p.read_text("utf-8").splitlines():
            _line = _line.strip()
            if not _line or _line.startswith("#") or "=" not in _line:
                continue
            _k, _v = _line.split("=", 1)
            _k = _k.strip()
            if _k and _k not in os.environ:
                os.environ[_k] = _v.strip()

TOKEN = (
    os.getenv("LOUNGE_BOT_TOKEN", "")
    or os.getenv("DISCORD_BOT_TOKEN", "")
    or os.getenv("DISCORD_TOKEN", "")
).strip()

GUILD_ID_STR = os.getenv("LANTERN_DISCORD_GUILD_ID", "").strip()
GUILD_ID: int | None = int(GUILD_ID_STR) if GUILD_ID_STR.isdigit() else None
DEFAULT_VC_NAME = os.getenv("LOUNGE_VOICE_CHANNEL", "Sinatra Lounge")

# ── Archive.org catalog ────────────────────────────────────────────────────────

# archive.org item identifiers for each mode.
# The bot resolves these to direct MP3 URLs at startup via the metadata API.
# To add more: find items at https://archive.org and add their identifiers here.
_CATALOG_IDS: dict[str, list[str]] = {
    "sinatra": [
        # Frank Sinatra radio broadcasts — old-time radio recordings (public domain)
        # Primary source: 217-episode radio collection (1940s–1950s shows)
        "FrankSinatraRadioCollection",   # 217 episodes: Your Hit Parade, A Date With Judy, etc.
        "Frank_Sinatra_Tape_1_1940",     # transcription disc Side A/B (~60 min/side)
        "YourHitParade19440506",         # Your Hit Parade 1944-05-06
        "file-002_20260213",             # Tommy Dorsey w/ Sinatra, Feb 24 1940 (52 MB)
    ],
    "dreams": [
        # Pure binaural beats — delta (0.5–4 Hz) and theta (4–8 Hz)
        # Delta induces deep sleep; theta is the hypnagogic/dreaming boundary
        "BrainwaveFrequenciesBinauralBeats",          # FreeDelta + FreeTheta (10 min each, clean pure tones)
        "RelaxingSleepMusic.DeltaWavesBinauralBeatsHealingForDeepSleepStressReliefMeditation",  # 20 tracks, 30–120 min each
        "deepsleepmusicforstressreliefhealingdeltabinauralbeatsforbrainpower",  # 15 long ambient tracks
    ],
    "focus": [
        # Pure binaural beats — alpha (8–14 Hz) and beta (14–30 Hz)
        # Alpha = relaxed focus, flow state; beta = active concentration
        "BrainwaveFrequenciesBinauralBeats",          # FreeAlpha + FreeBeta (10 min each, clean pure tones)
        "greenred-528-hz-music-with-healing-frequency",  # 5 hr 528 Hz ambient (Solfeggio tuning)
    ],
}

# Auto-search queries — used only when a mode has 0 seeded IDs.
_CATALOG_QUERIES: dict[str, str] = {
    "dreams": 'mediatype:audio subject:"binaural beats" (subject:"sleep" OR subject:"delta")',
    "focus":  'mediatype:audio subject:"binaural beats" (subject:"focus" OR subject:"alpha")',
}

# Per-mode filename filters: if set, only tracks whose name contains one of these
# substrings (case-insensitive) are included. None = accept all.
_MODE_FILENAME_FILTER: dict[str, list[str] | None] = {
    "sinatra": None,
    "dreams":  ["delta", "theta", "sleep", "dream", "relax", "heal"],
    "focus":   ["alpha", "beta", "focus", "528", "concent", "energy", "study"],
}

# ── Track model ────────────────────────────────────────────────────────────────

@dataclass
class Track:
    title: str
    url: str
    identifier: str   # archive.org item ID
    mode: str
    duration_secs: int = 0  # 0 = unknown

    def label(self) -> str:
        return f"**{self.title}** · _{self.identifier}_"


# ── Catalog resolution ─────────────────────────────────────────────────────────

def _fetch_json(url: str) -> dict | list | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "LanternLounge/1.0"})
        with urllib.request.urlopen(req, timeout=12) as r:
            return json.loads(r.read())
    except Exception as exc:
        print(f"  [warn] fetch failed {url[:80]}: {exc}")
        return None


def _resolve_item(identifier: str, mode: str) -> list[Track]:
    """Return MP3 tracks in an archive.org item, filtered for the given mode."""
    meta = _fetch_json(f"https://archive.org/metadata/{identifier}")
    if not meta or "files" not in meta:
        print(f"  [skip] {identifier} — no metadata")
        return []

    name_filters = _MODE_FILENAME_FILTER.get(mode)  # list[str] | None

    tracks = []
    for f in meta["files"]:
        name: str = f.get("name", "")
        fmt: str = f.get("format", "")
        name_lower = name.lower()

        # Only MP3 files
        if not name_lower.endswith(".mp3") and "mp3" not in fmt.lower():
            continue
        # Skip bitrate derivatives, playlists, jingles
        if any(name_lower.endswith(s) for s in ("_vbrmp3.m3u", ".m3u", "_64kb.mp3", "_128kb.mp3")):
            continue

        # Apply mode filename filter (keeps only contextually relevant tracks
        # when the same item is shared between modes, e.g. BrainwaveFrequencies)
        if name_filters and not any(kw in name_lower for kw in name_filters):
            continue

        try:
            size_bytes = int(f.get("size", 0))
        except (ValueError, TypeError):
            size_bytes = 999_999
        if size_bytes < 200_000:   # < 200 KB = noise / tiny clip
            continue

        title = (
            f.get("title")
            or name.rsplit("/", 1)[-1].rsplit(".", 1)[0].replace("_", " ")
        )
        url = f"https://archive.org/download/{identifier}/{urllib.parse.quote(name)}"
        try:
            secs = int(float(f.get("length", 0)))
        except (ValueError, TypeError):
            secs = 0

        tracks.append(Track(title=title, url=url, identifier=identifier, mode=mode, duration_secs=secs))

    if tracks:
        print(f"  [ok] {identifier} — {len(tracks)} track(s)")
    else:
        print(f"  [skip] {identifier} — no suitable MP3s for mode={mode}")
    return tracks


def _search_archive(query: str, rows: int = 6) -> list[str]:
    """Search archive.org and return up to `rows` item identifiers."""
    params = urllib.parse.urlencode({
        "q": query,
        "fl[]": "identifier",
        "rows": rows,
        "output": "json",
        "sort[]": "downloads desc",
    })
    data = _fetch_json(f"https://archive.org/advancedsearch.php?{params}")
    if not data:
        return []
    try:
        docs = data["response"]["docs"]
        return [d["identifier"] for d in docs if d.get("identifier")]
    except (KeyError, TypeError):
        return []


def build_catalog() -> dict[str, list[Track]]:
    """Resolve all catalog IDs + run searches for empty modes. Returns mode→tracks."""
    catalog: dict[str, list[Track]] = {}

    for mode, ids in _CATALOG_IDS.items():
        tracks: list[Track] = []
        # Use seeded IDs first
        if ids:
            print(f"[catalog] resolving {len(ids)} seeded items for mode={mode}")
            for ident in ids:
                tracks.extend(_resolve_item(ident, mode))
        # Fall back to search if still empty
        if not tracks and mode in _CATALOG_QUERIES:
            print(f"[catalog] searching archive.org for mode={mode} ...")
            found_ids = _search_archive(_CATALOG_QUERIES[mode], rows=6)
            print(f"  found {len(found_ids)} item(s): {found_ids}")
            for ident in found_ids:
                tracks.extend(_resolve_item(ident, mode))
        if not tracks:
            print(f"[catalog] WARNING: mode={mode} has no tracks. Add archive.org IDs to _CATALOG_IDS.")
        catalog[mode] = tracks

    return catalog


# ── Guild state ────────────────────────────────────────────────────────────────

@dataclass
class GuildState:
    voice_client: Optional[discord.VoiceClient] = None
    queue: list[Track] = field(default_factory=list)
    current: Optional[Track] = None
    mode: str = "sinatra"
    loop: bool = False
    volume: float = 0.7
    text_channel: Optional[discord.TextChannel] = None
    # Full per-mode shuffled lists (refill queue from here)
    _pool: dict[str, list[Track]] = field(default_factory=dict)


_STATES: dict[int, GuildState] = {}
_CATALOG: dict[str, list[Track]] = {}


def get_state(guild_id: int) -> GuildState:
    if guild_id not in _STATES:
        _STATES[guild_id] = GuildState()
    return _STATES[guild_id]


def _refill_queue(state: GuildState, mode: str) -> None:
    """Replenish queue from the shuffled pool for this mode."""
    pool = _CATALOG.get(mode, [])
    if not pool:
        return
    shuffled = list(pool)
    random.shuffle(shuffled)
    state._pool[mode] = shuffled
    state.queue.extend(shuffled)


def _ensure_queue(state: GuildState) -> None:
    """Make sure queue has at least a few tracks ahead."""
    if len(state.queue) < 3:
        _refill_queue(state, state.mode)


# ── Audio ──────────────────────────────────────────────────────────────────────

_FFMPEG_BEFORE = "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
_FFMPEG_OPTS = "-vn"


def _make_source(url: str, volume: float) -> discord.AudioSource:
    raw = discord.FFmpegPCMAudio(url, before_options=_FFMPEG_BEFORE, options=_FFMPEG_OPTS)
    return discord.PCMVolumeTransformer(raw, volume=volume)


def _make_after(guild_id: int, loop: asyncio.AbstractEventLoop):
    """Callback fired when a track finishes (runs in audio thread)."""
    def after(error: Exception | None):
        if error:
            print(f"[{guild_id}] audio error: {error}")
        asyncio.run_coroutine_threadsafe(_advance(guild_id), loop)
    return after


async def _advance(guild_id: int) -> None:
    """Play the next track in the queue."""
    state = get_state(guild_id)
    vc = state.voice_client

    if vc is None or not vc.is_connected():
        return

    if state.loop and state.current:
        track = state.current
    else:
        _ensure_queue(state)
        if not state.queue:
            state.current = None
            if state.text_channel:
                await state.text_channel.send("🎵 Queue empty — add more tracks or try `!shuffle`.")
            return
        track = state.queue.pop(0)

    state.current = track
    try:
        source = _make_source(track.url, state.volume)
        vc.play(source, after=_make_after(guild_id, asyncio.get_event_loop()))
        if state.text_channel:
            dur = f" `{track.duration_secs // 60}:{track.duration_secs % 60:02d}`" if track.duration_secs else ""
            await state.text_channel.send(f"▶️ Now playing: {track.label()}{dur}")
    except Exception as exc:
        print(f"[{guild_id}] play error: {exc}")
        if state.text_channel:
            await state.text_channel.send(f"⚠️ Could not play track: `{exc}`. Skipping...")
        await _advance(guild_id)


async def _join_voice(interaction_or_message, channel_name: str | None = None) -> tuple[discord.VoiceClient | None, str | None]:
    """
    Join a voice channel. Works with both slash Interaction and prefix Message.
    Returns (vc, error_string). error_string is None on success.
    """
    if isinstance(interaction_or_message, discord.Interaction):
        guild = interaction_or_message.guild
        author = interaction_or_message.user
    else:
        guild = interaction_or_message.guild
        author = interaction_or_message.author

    if guild is None:
        return None, "Must be used in a server."

    # Find target channel: explicit name > author's current vc > default vc name
    target_vc: discord.VoiceChannel | None = None
    if channel_name:
        target_vc = discord.utils.find(
            lambda c: isinstance(c, discord.VoiceChannel) and c.name.lower() == channel_name.lower(),
            guild.channels,
        )
    if target_vc is None and isinstance(author, discord.Member) and author.voice:
        target_vc = author.voice.channel  # type: ignore
    if target_vc is None:
        target_vc = discord.utils.find(
            lambda c: isinstance(c, discord.VoiceChannel) and DEFAULT_VC_NAME.lower() in c.name.lower(),
            guild.channels,
        )
    if target_vc is None:
        # Just grab first voice channel
        target_vc = next((c for c in guild.channels if isinstance(c, discord.VoiceChannel)), None)
    if target_vc is None:
        return None, "No voice channel found. Join one first or create a channel named 'Sinatra Lounge'."

    state = get_state(guild.id)
    vc = state.voice_client

    if vc and vc.is_connected():
        if vc.channel.id != target_vc.id:
            await vc.move_to(target_vc)
    else:
        try:
            vc = await target_vc.connect()
        except discord.ClientException as exc:
            return None, f"Could not connect: {exc}"

    state.voice_client = vc
    return vc, None


# ── Bot setup ──────────────────────────────────────────────────────────────────

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True
intents.voice_states = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


@client.event
async def on_ready():
    print(f"[READY] Lantern Lounge online as {client.user} (id={client.user.id})")
    print(f"[CATALOG] sinatra={len(_CATALOG.get('sinatra', []))} tracks  "
          f"dreams={len(_CATALOG.get('dreams', []))} tracks  "
          f"focus={len(_CATALOG.get('focus', []))} tracks")
    if GUILD_ID:
        guild_obj = discord.Object(id=GUILD_ID)
        tree.copy_global_to(guild=guild_obj)
        try:
            synced = await tree.sync(guild=guild_obj)
            print(f"[SYNC] {len(synced)} slash commands synced")
        except Exception as exc:
            print(f"[WARN] slash sync failed: {exc}")
    sys.stdout.flush()


# ── Helpers ────────────────────────────────────────────────────────────────────

async def _send(ctx, text: str, **kwargs):
    """Unified send — works for Interaction or Message."""
    if isinstance(ctx, discord.Interaction):
        if not ctx.response.is_done():
            await ctx.response.send_message(text, **kwargs)
        else:
            await ctx.followup.send(text, **kwargs)
    else:
        try:
            await ctx.channel.send(text, **kwargs)
        except discord.Forbidden:
            try:
                await ctx.author.send(f"(from Lounge)\n{text}")
            except discord.Forbidden:
                pass


def _mode_label(mode: str) -> str:
    return {"sinatra": "🎙️ Sinatra", "dreams": "🌙 Dreams", "focus": "🧠 Focus"}.get(mode, mode)


async def _start_mode(ctx, mode: str, channel_name: str | None = None) -> None:
    """Switch mode and start playing."""
    if isinstance(ctx, discord.Interaction):
        guild = ctx.guild
    else:
        guild = ctx.guild
    if guild is None:
        await _send(ctx, "Must be used in a server.")
        return

    state = get_state(guild.id)

    if not _CATALOG.get(mode):
        await _send(ctx, f"⚠️ No tracks loaded for mode `{mode}`. Check the catalog or add archive.org IDs.")
        return

    vc, err = await _join_voice(ctx, channel_name)
    if err:
        await _send(ctx, f"⚠️ {err}")
        return

    # Set text channel for now-playing announcements
    if isinstance(ctx, discord.Interaction):
        state.text_channel = ctx.channel  # type: ignore
    elif hasattr(ctx, "channel"):
        state.text_channel = ctx.channel

    was_same_mode = state.mode == mode
    state.mode = mode

    if vc and vc.is_playing():
        vc.stop()  # triggers after → _advance with new mode

    if not was_same_mode or not state.queue:
        state.queue.clear()
        _refill_queue(state, mode)

    await _send(ctx, f"{_mode_label(mode)} — starting playback ▶️")
    await _advance(guild.id)


# ── Prefix commands ────────────────────────────────────────────────────────────

@client.event
async def on_message(message: discord.Message):
    if message.author.bot or not message.guild:
        return

    content = (message.content or "").strip()
    lower = content.lower()

    if lower.startswith("!lounge") or lower.startswith("!sinatra"):
        parts = content.split(None, 1)
        channel_name = parts[1].strip() if len(parts) > 1 else None
        await _start_mode(message, "sinatra", channel_name)

    elif lower.startswith("!dreams") or lower.startswith("!dream-mode"):
        await _start_mode(message, "dreams")

    elif lower.startswith("!focus"):
        await _start_mode(message, "focus")

    elif lower in ("!skip", "!s", "!next"):
        state = get_state(message.guild.id)
        vc = state.voice_client
        if vc and vc.is_playing():
            vc.stop()  # after-callback triggers _advance
            await message.add_reaction("⏭️")
        else:
            await message.channel.send("Nothing playing.")

    elif lower in ("!stop", "!pause"):
        state = get_state(message.guild.id)
        vc = state.voice_client
        if vc and vc.is_playing():
            vc.pause()
            await message.channel.send("⏸️ Paused. `!resume` to continue.")
        else:
            await message.channel.send("Nothing playing.")

    elif lower in ("!resume", "!unpause"):
        state = get_state(message.guild.id)
        vc = state.voice_client
        if vc and vc.is_paused():
            vc.resume()
            await message.add_reaction("▶️")
        else:
            await message.channel.send("Nothing paused.")

    elif lower in ("!leave", "!bye", "!disconnect"):
        state = get_state(message.guild.id)
        vc = state.voice_client
        if vc and vc.is_connected():
            if vc.is_playing():
                vc.stop()
            await vc.disconnect()
            state.voice_client = None
            state.current = None
            await message.channel.send("👋 Disconnected from voice.")
        else:
            await message.channel.send("Not in a voice channel.")

    elif lower in ("!np", "!nowplaying", "!now"):
        state = get_state(message.guild.id)
        if state.current:
            vc = state.voice_client
            status = "▶️ Playing" if (vc and vc.is_playing()) else "⏸️ Paused"
            dur = (f" `{state.current.duration_secs // 60}:{state.current.duration_secs % 60:02d}`"
                   if state.current.duration_secs else "")
            loop_str = " 🔁" if state.loop else ""
            await message.channel.send(
                f"{status}{dur}{loop_str} — {state.current.label()}\n"
                f"Mode: {_mode_label(state.mode)}  Volume: {int(state.volume * 100)}%"
            )
        else:
            await message.channel.send("Nothing is playing. Try `!lounge`, `!dreams`, or `!focus`.")

    elif lower.startswith("!volume ") or lower.startswith("!vol "):
        parts = lower.split()
        if len(parts) < 2 or not parts[1].isdigit():
            await message.channel.send("Usage: `!volume 0-100`")
            return
        vol = max(0, min(100, int(parts[1]))) / 100.0
        state = get_state(message.guild.id)
        state.volume = vol
        vc = state.voice_client
        if vc and vc.source and hasattr(vc.source, "volume"):
            vc.source.volume = vol  # type: ignore
        await message.channel.send(f"🔊 Volume set to {int(vol * 100)}%")

    elif lower in ("!loop", "!repeat"):
        state = get_state(message.guild.id)
        state.loop = not state.loop
        await message.channel.send(f"🔁 Loop {'ON' if state.loop else 'OFF'}")

    elif lower in ("!queue", "!q"):
        state = get_state(message.guild.id)
        if not state.queue:
            await message.channel.send("Queue is empty. Playing from the pool when current track ends.")
            return
        lines = [f"**Queue** — mode: {_mode_label(state.mode)}"]
        for i, t in enumerate(state.queue[:10], 1):
            lines.append(f"`{i}.` {t.title}")
        if len(state.queue) > 10:
            lines.append(f"_...and {len(state.queue) - 10} more_")
        await message.channel.send("\n".join(lines))

    elif lower == "!shuffle":
        state = get_state(message.guild.id)
        random.shuffle(state.queue)
        await message.channel.send(f"🔀 Queue shuffled — {len(state.queue)} tracks ahead")

    elif lower == "!mode":
        state = get_state(message.guild.id)
        await message.channel.send(f"Current mode: {_mode_label(state.mode)}")

    elif lower.startswith("!catalog") or lower.startswith("!tracks"):
        parts = lower.split()
        mode = parts[1] if len(parts) > 1 and parts[1] in _CATALOG else None
        modes_to_show = [mode] if mode else list(_CATALOG.keys())
        lines = []
        for m in modes_to_show:
            tracks = _CATALOG.get(m, [])
            lines.append(f"**{_mode_label(m)}** — {len(tracks)} tracks")
            for t in tracks[:8]:
                lines.append(f"  • {t.title}")
            if len(tracks) > 8:
                lines.append(f"  _...and {len(tracks) - 8} more_")
        await message.channel.send("\n".join(lines) if lines else "No catalog loaded.")

    elif lower in ("!lounge-help", "!musichelp"):
        await message.channel.send(
            "**🎙️ Lantern Lounge Commands**\n```"
            "!lounge [channel]  — join voice + start Sinatra\n"
            "!dreams            — switch to binaural dreams\n"
            "!focus             — switch to binaural focus\n"
            "!skip / !s         — skip track\n"
            "!stop / !resume    — pause/resume\n"
            "!leave / !bye      — disconnect\n"
            "!np                — now playing\n"
            "!volume 0-100      — set volume\n"
            "!loop              — toggle loop\n"
            "!queue             — show upcoming\n"
            "!shuffle           — re-shuffle queue\n"
            "!mode              — current mode\n"
            "!catalog [mode]    — list loaded tracks\n"
            "```"
        )


# ── Slash commands ─────────────────────────────────────────────────────────────

@tree.command(name="lounge", description="Join voice and start Sinatra radio")
@app_commands.describe(channel="Voice channel to join (optional)")
async def cmd_lounge(interaction: discord.Interaction, channel: Optional[str] = None):
    await interaction.response.defer()
    await _start_mode(interaction, "sinatra", channel)


@tree.command(name="dreams", description="Switch to binaural beats for dreaming and sleep")
async def cmd_dreams(interaction: discord.Interaction):
    await interaction.response.defer()
    await _start_mode(interaction, "dreams")


@tree.command(name="focus", description="Switch to binaural beats for focus and flow")
async def cmd_focus(interaction: discord.Interaction):
    await interaction.response.defer()
    await _start_mode(interaction, "focus")


@tree.command(name="skip", description="Skip current track")
async def cmd_skip(interaction: discord.Interaction):
    state = get_state(interaction.guild_id)
    vc = state.voice_client
    if vc and vc.is_playing():
        vc.stop()
        await interaction.response.send_message("⏭️ Skipped.", ephemeral=True)
    else:
        await interaction.response.send_message("Nothing playing.", ephemeral=True)


@tree.command(name="leave", description="Stop playback and disconnect from voice")
async def cmd_leave(interaction: discord.Interaction):
    state = get_state(interaction.guild_id)
    vc = state.voice_client
    if vc and vc.is_connected():
        if vc.is_playing():
            vc.stop()
        await vc.disconnect()
        state.voice_client = None
        state.current = None
        await interaction.response.send_message("👋 Disconnected.", ephemeral=True)
    else:
        await interaction.response.send_message("Not connected.", ephemeral=True)


@tree.command(name="nowplaying", description="Show what's currently playing")
async def cmd_nowplaying(interaction: discord.Interaction):
    state = get_state(interaction.guild_id)
    if not state.current:
        await interaction.response.send_message("Nothing playing. Try `/lounge`, `/dreams`, or `/focus`.", ephemeral=True)
        return
    vc = state.voice_client
    status = "▶️" if (vc and vc.is_playing()) else "⏸️"
    dur = (f" `{state.current.duration_secs // 60}:{state.current.duration_secs % 60:02d}`"
           if state.current.duration_secs else "")
    embed = discord.Embed(title=f"{status} Now Playing", color=0xC9A84C)
    embed.add_field(name="Track", value=state.current.title, inline=False)
    embed.add_field(name="Source", value=f"`{state.current.identifier}`", inline=True)
    embed.add_field(name="Mode", value=_mode_label(state.mode), inline=True)
    embed.add_field(name="Volume", value=f"{int(state.volume * 100)}%", inline=True)
    if dur:
        embed.add_field(name="Duration", value=dur.strip(), inline=True)
    if state.loop:
        embed.set_footer(text="🔁 Loop is on")
    await interaction.response.send_message(embed=embed, ephemeral=True)


@tree.command(name="volume", description="Set playback volume (0–100)")
@app_commands.describe(level="Volume level 0–100")
async def cmd_volume(interaction: discord.Interaction, level: int):
    vol = max(0, min(100, level)) / 100.0
    state = get_state(interaction.guild_id)
    state.volume = vol
    vc = state.voice_client
    if vc and vc.source and hasattr(vc.source, "volume"):
        vc.source.volume = vol  # type: ignore
    await interaction.response.send_message(f"🔊 Volume: {int(vol * 100)}%", ephemeral=True)


@tree.error
async def on_slash_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    orig = getattr(error, "original", error)
    if isinstance(orig, discord.NotFound) and orig.code == 10062:
        return
    print(f"[SLASH ERROR] {type(orig).__name__}: {orig}")
    try:
        if not interaction.response.is_done():
            await interaction.response.send_message("Something went wrong.", ephemeral=True)
    except Exception:
        pass


# ── Auto-disconnect when alone ─────────────────────────────────────────────────

@client.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    """Leave voice if the bot is the only one left in the channel."""
    if member.bot:
        return
    state = get_state(member.guild.id)
    vc = state.voice_client
    if vc and vc.is_connected():
        human_members = [m for m in vc.channel.members if not m.bot]
        if not human_members:
            await asyncio.sleep(30)  # grace period — maybe they'll come back
            # Re-check
            vc = state.voice_client
            if vc and vc.is_connected():
                human_members = [m for m in vc.channel.members if not m.bot]
                if not human_members:
                    if vc.is_playing():
                        vc.stop()
                    await vc.disconnect()
                    state.voice_client = None
                    if state.text_channel:
                        await state.text_channel.send("🌙 Everyone left — Lantern Lounge disconnected.")


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    sys.stdout.reconfigure(encoding="utf-8")

    if not TOKEN:
        print("[FATAL] No token found. Set LOUNGE_BOT_TOKEN or DISCORD_BOT_TOKEN in .env")
        sys.exit(1)

    # Verify ffmpeg is available
    import shutil
    if not shutil.which("ffmpeg"):
        print("[FATAL] ffmpeg not found on PATH.")
        print("  Windows: winget install Gyan.FFmpeg")
        print("  macOS:   brew install ffmpeg")
        print("  Linux:   apt install ffmpeg")
        sys.exit(1)

    print("[INFO] Lantern Lounge Bot starting...")
    print(f"[INFO] Default voice channel: '{DEFAULT_VC_NAME}'")
    print("[INFO] Resolving archive.org catalog (this may take 10–20s)...")
    sys.stdout.flush()

    global _CATALOG
    _CATALOG = build_catalog()

    total = sum(len(v) for v in _CATALOG.values())
    print(f"[INFO] Catalog ready: {total} tracks across {len(_CATALOG)} modes")
    for mode, tracks in _CATALOG.items():
        print(f"  {_mode_label(mode)}: {len(tracks)} tracks")

    if total == 0:
        print("[WARN] No tracks loaded! Check your archive.org identifiers or internet connection.")

    sys.stdout.flush()
    client.run(TOKEN)


if __name__ == "__main__":
    main()
