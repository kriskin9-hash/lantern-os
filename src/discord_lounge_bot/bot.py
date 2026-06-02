"""
Lantern Discord Lounge Bot

Server-agnostic, channel-agnostic bot:
- listens to commands in any channel it can see;
- replies to !lantern-status with a safe health summary;
- slash commands work in any guild / any channel.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import os
import json
import re
import shutil
import sys
import time
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("lantern.bot")

try:
    import discord
    from discord import app_commands
except Exception as exc:
    logger.critical("Missing dependency 'discord.py': %s", exc)
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
KALSHI_PAPER_TICKETS_PATH = REPO_ROOT / "data" / "kalshi" / "kalshi-paper-trade-tickets-latest.json"
MAX_NOTEBOOK_TEXT_LENGTH = 2000

# Lantern image pack skill
sys.path.insert(0, str(REPO_ROOT / "skills" / "lantern-image-pack"))
try:
    import pack as image_pack
except Exception:
    image_pack = None

if not TOKEN:
    logger.critical("Missing DISCORD_BOT_TOKEN")
    sys.exit(1)

GUILD_ID_INT: int | None = None
CHANNEL_ID_INT: int | None = None

if GUILD_ID:
    try:
        GUILD_ID_INT = int(GUILD_ID)
    except ValueError:
        logger.warning("LANTERN_DISCORD_GUILD_ID is not a valid numeric ID — slash commands will sync globally only")
else:
    logger.warning("LANTERN_DISCORD_GUILD_ID not set — slash commands will sync globally only")

if CHANNEL_ID:
    try:
        CHANNEL_ID_INT = int(CHANNEL_ID)
    except ValueError:
        logger.warning("LANTERN_DISCORD_CHANNEL_ID is not a valid numeric ID — startup/pulse messages disabled")
else:
    logger.warning("LANTERN_DISCORD_CHANNEL_ID not set — startup/pulse messages disabled")

intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
intents.message_content = True
intents.voice_states = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# --------------------------------------------------------------------------- #
# Health pulse state
# --------------------------------------------------------------------------- #
HEALTH_PULSE_INTERVAL_SEC = 300   # 5 minutes — local log pulse
CHANNEL_PULSE_INTERVAL_SEC = 1800  # 30 minutes — Discord channel pulse
_health_state = {
    "started_at": time.time(),
    "pulse_count": 0,
    "last_pulse": 0.0,
    "last_channel_pulse": 0.0,
    "uptime_sec": 0.0,
    "latency_ms": 0.0,
}


def _update_health() -> None:
    """Refresh derived health metrics."""
    now = time.time()
    _health_state["uptime_sec"] = now - _health_state["started_at"]
    _health_state["last_pulse"] = now
    _health_state["pulse_count"] += 1


def _uptime_str() -> str:
    total = int(_health_state["uptime_sec"])
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{h}h {m}m {s}s"


async def health_pulse_loop() -> None:
    """Background task: log pulse every 5 min, post to channel every 30 min."""
    await client.wait_until_ready()
    while not client.is_closed():
        await asyncio.sleep(HEALTH_PULSE_INTERVAL_SEC)
        if client.is_closed():
            break

        _update_health()
        latency_ms = round(client.latency * 1000, 1) if client.latency else 0.0
        _health_state["latency_ms"] = latency_ms

        logger.info("Pulse #%s | uptime=%s | latency=%sms", _health_state['pulse_count'], _uptime_str(), latency_ms)

        now = time.time()
        if CHANNEL_ID_INT and now - _health_state["last_channel_pulse"] >= CHANNEL_PULSE_INTERVAL_SEC:
            channel = client.get_channel(CHANNEL_ID_INT)
            if channel:
                try:
                    await channel.send(
                        f":heartbeat: Lantern pulse #{_health_state['pulse_count']} | "
                        f"uptime {_uptime_str()} | latency {latency_ms}ms"
                    )
                    _health_state["last_channel_pulse"] = now
                except Exception:
                    logger.exception("Failed to send channel pulse")


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def status_text() -> str:
    return (
        "Lantern lounge bot online.\n"
        f"- time: {now_utc()}\n"
        f"- guild: {GUILD_ID_INT if GUILD_ID_INT else 'not set'}\n"
        f"- channel: {CHANNEL_ID_INT if CHANNEL_ID_INT else 'not set'}\n"
        f"- local status endpoint: {STATUS_URL}\n"
        f"- uptime: {_uptime_str()}\n"
        f"- pulses: {_health_state['pulse_count']}\n"
        f"- latency: {_health_state['latency_ms']}ms\n"
        "- commands: !lantern-status, !lantern-pulse, !lantern-voice-check, !dream, !note, !place, !character, !event, !lore, !symbol, !mirror, !recall, !odds, !one\n"
        "- slash commands: /dream"
    )


def pulse_text() -> str:
    return (
        f"Lantern pulse #{_health_state['pulse_count']}\n"
        f"- uptime: {_uptime_str()}\n"
        f"- latency: {_health_state['latency_ms']}ms\n"
        f"- last pulse: {datetime.fromtimestamp(_health_state['last_pulse'], tz=timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ') if _health_state['last_pulse'] else 'never'}\n"
        f"- started: {datetime.fromtimestamp(_health_state['started_at'], tz=timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}\n"
        f"- channel pulse interval: {CHANNEL_PULSE_INTERVAL_SEC // 60}min\n"
        f"- log pulse interval: {HEALTH_PULSE_INTERVAL_SEC // 60}min"
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


def format_odds(limit: int = 5) -> str:
    if not KALSHI_PAPER_TICKETS_PATH.exists():
        return "No paper trade tickets found. Run the Kalshi watchlist pipeline first."
    try:
        data = json.loads(KALSHI_PAPER_TICKETS_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return f"Could not read paper tickets: {exc}"
    tickets = data.get("tickets", [])
    if not tickets:
        return "Paper ticket file loaded but contains no tickets."
    budget = data.get("budgetPolicy", {})
    lines = [
        f"Kalshi paper odds — {data.get('ticketCount', len(tickets))} tickets, "
        f"bankroll ${budget.get('bankrollUsd', '?')}, "
        f"remaining daily risk ${budget.get('remainingDailyPaperRiskUsd', '?')}",
        f"Generated: {data.get('generatedAt', 'unknown')}",
        "",
    ]
    for ticket in tickets[:limit]:
        title = ticket.get("title", "?")
        if len(title) > 80:
            title = title[:77] + "..."
        side = ticket.get("side", "?")
        cents = ticket.get("suggestedLimitCents", "?")
        rank = ticket.get("rank", "?")
        days = ticket.get("daysToClose", "?")
        edge = ticket.get("edgeLabel", "")
        edge_str = f" ({edge})" if edge else ""
        lines.append(f"#{rank} {side}@{cents}c{edge_str} | {days}d | {title}")
    if len(tickets) > limit:
        lines.append(f"... and {len(tickets) - limit} more tickets.")
    lines.append("")
    lines.append(data.get("boundary", "Paper only. Not investment advice."))
    return "\n".join(lines)


@tree.command(name="dream", description="Save a dream to your private Lantern notebook")
@app_commands.describe(text="Describe your dream")
async def slash_dream(interaction: discord.Interaction, text: str):
    try:
        append_notebook_entry(interaction.user, "dream", text)
        await interaction.response.send_message("Dream saved to your private local Lantern notebook.", ephemeral=True)
    except ValueError:
        await interaction.response.send_message("Write something after `/dream`.", ephemeral=True)
    except Exception:
        logger.exception("Failed to save dream for user %s", interaction.user)
        await interaction.response.send_message("Failed to save dream. The team has been notified.", ephemeral=True)


@client.event
async def on_ready():
    logger.info("Logged in as %s at %s", client.user, now_utc())
    _health_state["started_at"] = time.time()
    _health_state["pulse_count"] = 0
    _health_state["last_pulse"] = 0.0
    _health_state["last_channel_pulse"] = 0.0

    # Start background health pulse
    client.loop.create_task(health_pulse_loop())
    logger.info("Health pulse loop started")

    if CHANNEL_ID_INT:
        channel = client.get_channel(CHANNEL_ID_INT)
        if channel:
            try:
                await channel.send(status_text())
            except Exception:
                logger.exception("Failed to send startup status message")
        else:
            logger.warning("Primary channel not found in cache — startup status skipped")

    try:
        if GUILD_ID_INT:
            guild = discord.Object(id=GUILD_ID_INT)
            tree.copy_global_to(guild=guild)
            await tree.sync(guild=guild)
            logger.info("Slash commands synced to guild %s", GUILD_ID_INT)
        await tree.sync()
        logger.info("Slash commands synced globally")
    except Exception:
        logger.exception("Failed to sync slash commands")


@client.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    raw_content = message.content.strip()
    content = raw_content.lower()
    if content == "!lantern-status":
        await message.reply(status_text())
    elif content == "!lantern-pulse":
        await message.reply(pulse_text())
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
        except Exception:
            logger.exception("Mirror failed for user %s", message.author)
            await message.reply("Mirror failed. The team has been notified.")
    elif content == "!recall" or content.startswith("!recall "):
        query = raw_content[len("!recall"):].strip()
        await message.reply(format_recall(recall_notebook_entries(message.author, query)))
    elif content == "!odds" or content.startswith("!odds "):
        limit = 5
        args = raw_content[len("!odds"):].strip()
        if args.isdigit():
            limit = max(1, min(20, int(args)))
        await message.reply(format_odds(limit))
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
        except Exception:
            logger.exception("Pack generation failed")
            await message.reply("Pack generation failed. The team has been notified.")
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
        logger.warning("Playback error: %s", error)
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
        except Exception:
            logger.exception("Loop playback failed")


@client.event
async def on_error(event_method: str, /, *args, **kwargs):
    """Global Discord event error handler — logs full traceback."""
    logger.exception("Unhandled exception in event %s", event_method)

def main():
    logger.info("Starting Lantern Discord lounge bot...")
    logger.info("No secrets are printed. Stop with Ctrl+C.")
    client.run(TOKEN)


if __name__ == "__main__":
    main()
