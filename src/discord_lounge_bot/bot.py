"""
Lantern Discord Lounge Bot

Status-only bot for one allowlisted channel:
- posts startup status in the configured channel;
- replies to !lantern-status with a safe health summary;
- ignores all other channels.
"""

from __future__ import annotations

import hashlib
import os
import json
import re
import shutil
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

try:
    import discord
except Exception as exc:
    print(f"[FATAL] Missing dependency 'discord.py': {exc}")
    print("Install with: pip install discord.py")
    sys.exit(1)


TOKEN = os.getenv("DISCORD_BOT_TOKEN", "").strip()
GUILD_ID = os.getenv("LANTERN_DISCORD_GUILD_ID", "").strip()
CHANNEL_ID = os.getenv("LANTERN_DISCORD_CHANNEL_ID", "").strip()
STATUS_URL = os.getenv("LANTERN_STATUS_URL", "http://127.0.0.1:5001/api/status").strip()
VOICE_CHANNEL_ID = os.getenv("LANTERN_VOICE_CHANNEL_ID", "").strip()
VOICE_CHANNEL_NAME = os.getenv("LANTERN_VOICE_CHANNEL", "Lounge").strip()
RADIO_URL = os.getenv("LANTERN_RADIO_URL", "").strip()
TEST_SERVER_INVITE = "https://discord.gg/xmsbPjMGm"
ENABLE_VOICE = os.getenv("LANTERN_DISCORD_ENABLE_VOICE", "").strip().lower() in {"1", "true", "yes", "on"}
ENABLE_RADIO = os.getenv("LANTERN_DISCORD_ENABLE_RADIO", "").strip().lower() in {"1", "true", "yes", "on"}
REPO_ROOT = Path(__file__).resolve().parents[2]
DREAMER_NOTEBOOK_DIR = REPO_ROOT / "data" / "dreamer" / "notebooks"
MAX_NOTEBOOK_TEXT_LENGTH = 2000

# Lantern image pack skill
sys.path.insert(0, str(REPO_ROOT / "skills" / "lantern-image-pack"))
try:
    import pack as image_pack
except Exception:
    image_pack = None

if not TOKEN:
    print("[FATAL] Missing DISCORD_BOT_TOKEN")
    sys.exit(1)
if not GUILD_ID:
    print("[FATAL] Missing LANTERN_DISCORD_GUILD_ID")
    sys.exit(1)
if not CHANNEL_ID:
    print("[FATAL] Missing LANTERN_DISCORD_CHANNEL_ID")
    sys.exit(1)

try:
    GUILD_ID_INT = int(GUILD_ID)
    CHANNEL_ID_INT = int(CHANNEL_ID)
except ValueError:
    print("[FATAL] Guild/channel IDs must be numeric Discord snowflakes.")
    sys.exit(1)

intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
intents.message_content = True
intents.voice_states = True

client = discord.Client(intents=intents)


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def status_text() -> str:
    return (
        "Lantern lounge bot online.\n"
        f"- time: {now_utc()}\n"
        f"- guild: {GUILD_ID_INT}\n"
        f"- channel: {CHANNEL_ID_INT}\n"
        f"- local status endpoint: {STATUS_URL}\n"
        "- commands: !lantern-status, !lantern-voice-check, !dream, !note, !place, !character, !event, !lore, !symbol, !mirror, !recall, !one"
    )


def voice_status_text() -> str:
    target = VOICE_CHANNEL_ID or VOICE_CHANNEL_NAME or "not configured"
    return (
        "Lantern voice gate.\n"
        f"- target: {target}\n"
        f"- voice enabled: {ENABLE_VOICE}\n"
        f"- radio enabled: {ENABLE_RADIO}\n"
        f"- radio url configured: {bool(RADIO_URL)}\n"
        f"- ffmpeg on PATH: {bool(shutil.which('ffmpeg'))}\n"
        "- join command: !lantern-join-lounge\n"
        "- radio command: !lantern-radio\n"
        "- boundary: no auto-join, no autoplay, no shell/MCP execution from Discord"
    )


def find_voice_channel(guild: discord.Guild):
    if VOICE_CHANNEL_ID:
        try:
            channel_id = int(VOICE_CHANNEL_ID)
        except ValueError:
            return None
        return discord.utils.get(guild.voice_channels, id=channel_id)
    if VOICE_CHANNEL_NAME:
        return discord.utils.find(lambda channel: channel.name.lower() == VOICE_CHANNEL_NAME.lower(), guild.voice_channels)
    return None


def notebook_user_id(author: discord.abc.User) -> str:
    return f"discord-{author.id}"


def notebook_path(user_id: str) -> Path:
    safe = re.sub(r"[^a-zA-Z0-9._-]+", "-", user_id).strip("-").lower() or "discord-user"
    return DREAMER_NOTEBOOK_DIR / f"{safe}.jsonl"


def generate_entry_id() -> str:
    return str(uuid.uuid4())


def generate_ternary_id(seed: str = "") -> str:
    base = seed or str(uuid.uuid4())
    h = hashlib.sha256(base.encode("utf-8")).hexdigest()
    val = int(h[:16], 16)
    digits = []
    for _ in range(12):
        digits.append(str(val % 3))
        val //= 3
    return "".join(reversed(digits))


def append_notebook_entry(author: discord.abc.User, kind: str, text: str, name: str = "", mood: str = "", links: list = None) -> dict:
    clean_text = text.strip()[:MAX_NOTEBOOK_TEXT_LENGTH]
    if not clean_text:
        raise ValueError("text_required")
    user_id = notebook_user_id(author)
    entry_id = generate_entry_id()
    record = {
        "id": entry_id,
        "recordedAt": now_utc(),
        "user": user_id,
        "kind": kind,
        "source": "discord",
        "discordAuthorId": str(author.id),
        "discordAuthorName": str(author),
        "text": clean_text,
        "name": name or None,
        "mood": mood or None,
        "links": links or [],
        "tags": [],
        "ternaryId": generate_ternary_id(entry_id + clean_text),
        "private": True,
    }
    path = notebook_path(user_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record


def recall_notebook_entries(author: discord.abc.User, query: str, limit: int = 5) -> list[dict]:
    path = notebook_path(notebook_user_id(author))
    if not path.exists():
        return []
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    needle = query.strip().lower()
    if needle:
        rows = [row for row in rows if needle in str(row.get("text", "")).lower()]
    return rows[-limit:]


def format_recall(entries: list[dict]) -> str:
    if not entries:
        return "No matching private notebook entries found."
    lines = ["Private notebook recall:"]
    for entry in reversed(entries):
        text = str(entry.get("text", "")).replace("\n", " ").strip()
        if len(text) > 160:
            text = text[:157] + "..."
        tid = entry.get("ternaryId", "")
        tid_str = f" [{tid}]" if tid else ""
        lines.append(f"- {entry.get('kind', 'note')}{tid_str} at {entry.get('recordedAt', 'unknown')}: {text}")
    return "\n".join(lines)


async def connect_to_lounge(message: discord.Message):
    if not ENABLE_VOICE:
        await message.reply("Voice join is held. Set LANTERN_DISCORD_ENABLE_VOICE=true after P0 health checks pass.")
        return None
    if message.guild is None:
        await message.reply("Voice join needs a guild context.")
        return None
    channel = find_voice_channel(message.guild)
    if channel is None:
        await message.reply("Configured Lounge voice channel was not found. Run Test-DiscordBotHealth.ps1 first.")
        return None
    if message.guild.voice_client and message.guild.voice_client.is_connected():
        await message.reply(f"Lantern is already connected to {message.guild.voice_client.channel.name}.")
        return message.guild.voice_client
    voice_client = await channel.connect()
    await message.reply(f"Lantern joined {channel.name}.")
    return voice_client


@client.event
async def on_ready():
    print(f"[READY] Logged in as {client.user} at {now_utc()}")
    channel = client.get_channel(CHANNEL_ID_INT)
    if channel is None:
        print("[WARN] Configured channel was not found in cache. Check bot permissions and IDs.")
        return
    try:
        await channel.send(status_text())
    except Exception as exc:
        print(f"[WARN] Failed to send startup status message: {exc}")


@client.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    if message.channel.id != CHANNEL_ID_INT:
        return
    raw_content = message.content.strip()
    content = raw_content.lower()
    if content == "!lantern-status":
        await message.reply(status_text())
    elif content == "!lantern-voice-check":
        await message.reply(voice_status_text())
    elif content.startswith("!dream "):
        try:
            append_notebook_entry(message.author, "dream", raw_content[len("!dream "):])
            await message.reply("Dream saved to your private local Lantern notebook.")
        except ValueError:
            await message.reply("Write the dream after `!dream`.")
    elif content.startswith("!note "):
        try:
            append_notebook_entry(message.author, "note", raw_content[len("!note "):])
            await message.reply("Note saved to your private local Lantern notebook.")
        except ValueError:
            await message.reply("Write the note after `!note`.")
    elif content.startswith("!place "):
        try:
            append_notebook_entry(message.author, "place", raw_content[len("!place "):])
            await message.reply("Place saved to your private local Lantern notebook.")
        except ValueError:
            await message.reply("Write the place after `!place`.")
    elif content.startswith("!character "):
        try:
            append_notebook_entry(message.author, "character", raw_content[len("!character "):])
            await message.reply("Character saved to your private local Lantern notebook.")
        except ValueError:
            await message.reply("Write the character after `!character`.")
    elif content.startswith("!event "):
        try:
            append_notebook_entry(message.author, "event", raw_content[len("!event "):])
            await message.reply("Event saved to your private local Lantern notebook.")
        except ValueError:
            await message.reply("Write the event after `!event`.")
    elif content.startswith("!lore "):
        try:
            append_notebook_entry(message.author, "lore", raw_content[len("!lore "):])
            await message.reply("Lore saved to your private local Lantern notebook.")
        except ValueError:
            await message.reply("Write the lore after `!lore`.")
    elif content.startswith("!symbol "):
        try:
            append_notebook_entry(message.author, "symbol", raw_content[len("!symbol "):])
            await message.reply("Symbol saved to your private local Lantern notebook.")
        except ValueError:
            await message.reply("Write the symbol after `!symbol`.")
    elif content == "!mirror":
        try:
            user_id = notebook_user_id(message.author)
            entries = recall_notebook_entries(message.author, "", limit=500)
            ids = [e.get("id") for e in entries if e.get("kind") != "mirror" and e.get("id")]
            if len(ids) == 0:
                await message.reply("No facets to mirror yet. Drop something in the well first.")
                return
            mirror_text = f"Mirror of {len(ids)} facets"
            record = append_notebook_entry(message.author, "mirror", mirror_text)
            await message.reply(f"Mirrored {len(ids)} facets into a new mirror entry.")
        except Exception as exc:
            await message.reply(f"Mirror failed: {exc}")
    elif content == "!recall" or content.startswith("!recall "):
        query = raw_content[len("!recall"):].strip()
        await message.reply(format_recall(recall_notebook_entries(message.author, query)))
    elif content == "!one" or content.startswith("!one "):
        args = raw_content[len("!one"):].strip()
        if not args:
            args = "Spain founder route trip"
        if image_pack is None:
            await message.reply("Image pack skill is not available. Check `skills/lantern-image-pack/`.")
            return
        try:
            # 20 scenes from the Lantern OS Spain/Paris founder route
            spain_scenes = [
                "Spanish Abode at dawn — retrofitted villa, warm stone walls, workshop lights on",
                "Founder packing the field van — calibration kit, ring tools, dependency packet",
                "Open road leaving the Spanish Abode — coastal highway, olive groves, morning mist",
                "Madrid skyline approach — Gran Via golden hour, traffic flowing toward the city",
                "Madrid workshop pause — tuning equipment on a workbench, café con leche nearby",
                "Highway to Zaragoza — arid meseta landscape, distant wind turbines, van in mirror",
                "Zaragoza old town square — Basilica del Pilar, founder sketching route notes",
                "Night stop in Zaragoza — van parked under street lamps, guardian figure silhouette",
                "Coastal run toward Barcelona — Mediterranean blue, cliffs, tunnel of trees",
                "Barcelona harbor view — port cranes, sailboats, Sagrada Familia distant spires",
                "Barcelona market morning — fresh fruit stalls, local radio, route map on table",
                "Crossing into France — border sign, changing road markings, van clock shifts",
                "Montpellier vineyards — rows of green, stone farmhouse, sun low and long",
                "Lyon approach at dusk — Rhône river reflection, city lights climbing the hill",
                "Lyon bridge crossing — stone arches, tram sparks, two guardian figures walking",
                "Northern France sunrise — flat fields, poplar trees, fog lifting off canals",
                "Paris periphery — highway ring, first glimpse of La Défense skyline",
                "Paris Roads endpoint — cobblestone street, café terrace, founder packet on table",
                "Ring mechanism intake — close-up of hands calibrating, public-safe shell only",
                "Rose mechanism dependency lane — symbolic rose, technical sheet, held boundary",
            ]
            title = f"Lantern OS — {args}"
            pack_dir = image_pack.make_pack(title, len(spain_scenes), [f"{i+1:02d}.png" for i in range(len(spain_scenes))])
            # Write scene prompts as a companion text file
            prompts_path = pack_dir / "image-prompts.txt"
            lines = [f"{i+1:02d}. {scene}" for i, scene in enumerate(spain_scenes)]
            prompts_path.write_text("\n".join(lines), encoding="utf-8")
            await message.reply(
                f"Generated `{title}` image pack with {len(spain_scenes)} scenes.\n"
                f"Path: `{pack_dir}`\n"
                f"Open `index.html` locally to preview.\n"
                f"`image-prompts.txt` contains the 20 scene descriptions for generation."
            )
        except Exception as exc:
            await message.reply(f"Pack generation failed: {exc}")
    elif content == "!lantern-join-lounge":
        await connect_to_lounge(message)
    elif content == "!lantern-leave-lounge":
        if message.guild and message.guild.voice_client and message.guild.voice_client.is_connected():
            await message.guild.voice_client.disconnect()
            await message.reply("Lantern left Lounge.")
        else:
            await message.reply("Lantern is not connected to a voice channel.")
    elif content == "!lantern-radio":
        if not ENABLE_RADIO:
            await message.reply("Radio is held. Set LANTERN_DISCORD_ENABLE_RADIO=true and LANTERN_RADIO_URL after rights and P0 checks pass.")
            return
        if not RADIO_URL:
            await message.reply("Radio URL is not configured. Set LANTERN_RADIO_URL to a rights-checked stream or local file.")
            return
        if not shutil.which("ffmpeg"):
            await message.reply("ffmpeg is missing on PATH, so radio playback is blocked.")
            return
        voice_client = await connect_to_lounge(message)
        if voice_client is None:
            return
        _start_playback(voice_client, RADIO_URL)
        await message.reply("Lantern radio started from the configured rights-checked source.")
    elif content.startswith("!lantern-play "):
        url = raw_content[len("!lantern-play "):].strip()
        if not url:
            await message.reply("Provide a URL or local file path after `!lantern-play`.")
            return
        if not shutil.which("ffmpeg"):
            await message.reply("ffmpeg is missing on PATH, so playback is blocked.")
            return
        voice_client = await connect_to_lounge(message)
        if voice_client is None:
            return
        _start_playback(voice_client, url)
        await message.reply(f"Lantern playing: {url}")
    elif content == "!lantern-loop":
        if not message.guild:
            await message.reply("Loop toggle needs a guild context.")
            return
        vc = message.guild.voice_client
        if not vc or not vc.is_connected():
            await message.reply("Lantern is not in a voice channel. Join first with `!lantern-join-lounge`.")
            return
        vc._lantern_loop = not getattr(vc, "_lantern_loop", False)
        state = "on" if vc._lantern_loop else "off"
        await message.reply(f"Loop mode: {state}.")


def _start_playback(voice_client, source_url):
    if voice_client.is_playing():
        voice_client._lantern_current_url = None
        voice_client.stop()
    voice_client._lantern_current_url = source_url
    voice_client._lantern_loop = getattr(voice_client, "_lantern_loop", False)
    voice_client.play(
        discord.FFmpegPCMAudio(source_url),
        after=lambda error: _after_playback(error, voice_client),
    )


def _after_playback(error, voice_client):
    if error:
        print(f"[WARN] Playback error: {error}")
        return
    if not voice_client or not voice_client.is_connected():
        return
    url = getattr(voice_client, "_lantern_current_url", None)
    loop = getattr(voice_client, "_lantern_loop", False)
    if url and loop:
        try:
            voice_client.play(
                discord.FFmpegPCMAudio(url),
                after=lambda err: _after_playback(err, voice_client),
            )
        except Exception as exc:
            print(f"[WARN] Loop playback failed: {exc}")


def main():
    print("[INFO] Starting Lantern Discord lounge bot...")
    print("[INFO] No secrets are printed. Stop with Ctrl+C.")
    client.run(TOKEN)


if __name__ == "__main__":
    main()
