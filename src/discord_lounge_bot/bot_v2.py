"""
Lantern OS Discord Bot v2 — Slash Commands + Role Gating

Generated: 2026-05-31.
Purpose: monetized Discord server with tiered access and slash commands.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

try:
    import discord
    from discord import app_commands
except Exception as exc:
    print(f"[FATAL] Missing dependency 'discord.py': {exc}")
    sys.exit(1)

# MCP Bridge — optional integration with orchestrator
try:
    from mcp_bridge import MCPBridge, get_bridge
    MCP_AVAILABLE = True
except ImportError as e:
    MCP_AVAILABLE = False
    get_bridge = None
    print(f"[INFO] MCP Bridge not available: {e}")

# Lantern Archive Curator — Internet Archive media streaming
try:
    from archive_curator import get_curator, SINATRA_COLLECTION
    ARCHIVE_AVAILABLE = True
except ImportError as e:
    ARCHIVE_AVAILABLE = False
    get_curator = None
    print(f"[INFO] Archive Curator not available: {e}")

# Voice Curator — Frank Sinatra playback in lounge
try:
    from voice_curator import get_voice_player, get_sinatra
    VOICE_AVAILABLE = True
except ImportError as e:
    VOICE_AVAILABLE = False
    get_voice_player = None
    get_sinatra = None
    print(f"[INFO] Voice Curator not available: {e}")

# Cognitive Dream Journal — fallacy detection + persistent characters
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "skills" / "dream_journal"))
try:
    from cognitive_layer import get_cognitive_journal
    COGNITIVE_AVAILABLE = True
except ImportError as e:
    COGNITIVE_AVAILABLE = False
    get_cognitive_journal = None
    print(f"[INFO] Cognitive Dream Journal not available: {e}")

# ── Configuration ──
TOKEN = os.getenv("DISCORD_BOT_TOKEN", "").strip()
GUILD_ID = os.getenv("LANTERN_DISCORD_GUILD_ID", "").strip()
STATUS_URL = os.getenv("LANTERN_STATUS_URL", "http://127.0.0.1:4177/api/status").strip()
REPO_ROOT = Path(__file__).resolve().parents[2]
DREAMER_NOTEBOOK_DIR = REPO_ROOT / "data" / "dreamer" / "notebooks"
SUBSCRIBER_DATA_PATH = Path(os.getenv("SUBSCRIBER_DATA_PATH", REPO_ROOT / "data" / "discord" / "subscribers.json"))
KALSHI_PAPER_TICKETS_PATH = REPO_ROOT / "data" / "kalshi" / "kalshi-paper-trade-tickets-latest.json"
MAX_NOTEBOOK_TEXT_LENGTH = 2000

# Role name constants (case-insensitive matching)
ROLE_PUBLIC = "@everyone"
ROLE_SUPPORTER = "supporter"
ROLE_PILOT = "pilot"
ROLE_FOUNDER = "founder"

TIER_ORDER = {ROLE_PUBLIC: 0, ROLE_SUPPORTER: 1, ROLE_PILOT: 2, ROLE_FOUNDER: 3}

# ── Environment checks ──
if not TOKEN:
    print("[FATAL] Missing DISCORD_BOT_TOKEN")
    sys.exit(1)

try:
    GUILD_ID_INT = int(GUILD_ID) if GUILD_ID else None
except ValueError:
    print("[FATAL] LANTERN_DISCORD_GUILD_ID must be numeric")
    sys.exit(1)

# ── Discord client setup ──
intents = discord.Intents.default()
intents.guilds = True
intents.voice_states = True  # For voice channel features
# Note: members and message_content require privileged intents enabled in Discord Developer Portal
# intents.members = True  # Uncomment if needed and intents are enabled
# intents.message_content = True  # Uncomment if needed and intents are enabled

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# ── Helpers ──

def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def notebook_user_id(user: discord.User | discord.Member) -> str:
    return f"discord-{user.id}"


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


def append_notebook_entry(user: discord.User | discord.Member, kind: str, text: str, **kwargs) -> dict:
    clean_text = text.strip()[:MAX_NOTEBOOK_TEXT_LENGTH]
    if not clean_text:
        raise ValueError("text_required")
    user_id = notebook_user_id(user)
    entry_id = generate_entry_id()
    record = {
        "id": entry_id,
        "recordedAt": now_utc(),
        "user": user_id,
        "kind": kind,
        "source": "discord",
        "discordAuthorId": str(user.id),
        "discordAuthorName": str(user),
        "text": clean_text,
        "name": kwargs.get("name") or None,
        "mood": kwargs.get("mood") or None,
        "links": kwargs.get("links", []),
        "tags": kwargs.get("tags", []),
        "ternaryId": generate_ternary_id(entry_id + clean_text),
        "private": True,
    }
    path = notebook_path(user_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record


def recall_notebook_entries(user: discord.User | discord.Member, query: str = "", limit: int = 5) -> list[dict]:
    path = notebook_path(notebook_user_id(user))
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
        return "No matching notebook entries found."
    lines = ["Notebook recall:"]
    for entry in reversed(entries):
        text = str(entry.get("text", "")).replace("\n", " ").strip()
        if len(text) > 160:
            text = text[:157] + "..."
        tid = entry.get("ternaryId", "")
        tid_str = f" [{tid}]" if tid else ""
        lines.append(f"- {entry.get('kind', 'note')}{tid_str} at {entry.get('recordedAt', 'unknown')}: {text}")
    return "\n".join(lines)


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


def get_user_tier(member: discord.Member) -> str:
    """Return the highest tier role the user has."""
    role_names = {r.name.lower() for r in member.roles}
    if ROLE_FOUNDER in role_names:
        return ROLE_FOUNDER
    if ROLE_PILOT in role_names:
        return ROLE_PILOT
    if ROLE_SUPPORTER in role_names:
        return ROLE_SUPPORTER
    return ROLE_PUBLIC


def require_tier(minimum: str):
    """Decorator to gate slash commands by role tier. (DEBUG MODE: disabled for testing)"""
    # All commands free during debug mode — return empty decorator
    def noop(func):
        return func
    return noop


# ── Slash Commands ──

@tree.command(name="status", description="Lantern OS health summary")
async def cmd_status(interaction: discord.Interaction):
    embed = discord.Embed(title="Lantern OS Status", color=0x0d9488)
    embed.add_field(name="Time", value=now_utc(), inline=False)
    embed.add_field(name="Service", value="lantern-garage", inline=True)
    embed.add_field(name="Tier", value=get_user_tier(interaction.user).title(), inline=True)
    embed.set_footer(text="Local-first. Evidence-backed.")
    await interaction.response.send_message(embed=embed)


@tree.command(name="help", description="List available commands for your tier")
async def cmd_help(interaction: discord.Interaction):
    tier = get_user_tier(interaction.user)
    embed = discord.Embed(title="Lantern OS Commands", color=0x2563eb)
    embed.add_field(name="Public", value="`/status`, `/help`, `/subscribe`, `/music`, `/art`, `/movies`", inline=False)
    if tier in (ROLE_SUPPORTER, ROLE_PILOT, ROLE_FOUNDER):
        embed.add_field(name="Supporter+", value="`/dream`, `/note`, `/wish`, `/recall`, `/mirror`, `/wallet`, `/odds`, `/talk`", inline=False)
    if tier in (ROLE_PILOT, ROLE_FOUNDER):
        embed.add_field(name="Pilot+", value="`/converge`, `/rag-status`, `/queue`, `/place`, `/character`, `/symbol`", inline=False)
    if tier == ROLE_FOUNDER:
        embed.add_field(name="Founder", value="`/dispatch`, `/controls`, `/boot-check`, `/release-gate`", inline=False)
    embed.add_field(name="🎵 Music & Voice", value="`/sing`, `/nextsong`, `/stop`, `/leave` — Frank Sinatra from Internet Archive", inline=False)
    embed.set_footer(text=f"Your tier: {tier.title()}")
    await interaction.response.send_message(embed=embed, ephemeral=True)


@tree.command(name="subscribe", description="Payment system (DEBUG MODE: disabled)")
async def cmd_subscribe(interaction: discord.Interaction):
    embed = discord.Embed(title=" Payment System — DEBUG MODE", color=0xf59e0b)
    embed.description = "**All features unlocked for testing.** Payment bridge disabled until production launch."
    embed.add_field(name="Supporter Tier", value="$20/month (coming soon)", inline=False)
    embed.add_field(name="Pilot Tier", value="$200/month (coming soon)", inline=False)
    embed.add_field(name="Public Tier", value="Free (all features active now)", inline=False)
    embed.set_footer(text="Payment system will connect to Patreon at launch.")
    await interaction.response.send_message(embed=embed, ephemeral=True)


@tree.command(name="dream", description="Save a dream to your private notebook")
@app_commands.describe(text="What did you see?")
@require_tier(ROLE_SUPPORTER)
async def cmd_dream(interaction: discord.Interaction, text: str):
    record = append_notebook_entry(interaction.user, "dream", text)
    await interaction.response.send_message(f"Dream saved. ID: `{record['id']}`", ephemeral=True)


@tree.command(name="note", description="Save a note to your private notebook")
@app_commands.describe(text="What do you want to remember?")
@require_tier(ROLE_SUPPORTER)
async def cmd_note(interaction: discord.Interaction, text: str):
    record = append_notebook_entry(interaction.user, "note", text)
    await interaction.response.send_message(f"Note saved. ID: `{record['id']}`", ephemeral=True)


@tree.command(name="wish", description="Save a wish to your private notebook")
@app_commands.describe(text="What do you wish for?")
@require_tier(ROLE_SUPPORTER)
async def cmd_wish(interaction: discord.Interaction, text: str):
    record = append_notebook_entry(interaction.user, "wish", text)
    await interaction.response.send_message(f"Wish saved behind the door. ID: `{record['id']}`", ephemeral=True)


@tree.command(name="recall", description="Search your private notebook")
@app_commands.describe(query="Search query (empty for latest)")
@require_tier(ROLE_SUPPORTER)
async def cmd_recall(interaction: discord.Interaction, query: Optional[str] = None):
    entries = recall_notebook_entries(interaction.user, query or "", limit=10)
    text = format_recall(entries)
    if len(text) > 1900:
        text = text[:1897] + "..."
    await interaction.response.send_message(f"```{text}```", ephemeral=True)


@tree.command(name="mirror", description="Mirror all your notebook facets")
@require_tier(ROLE_SUPPORTER)
async def cmd_mirror(interaction: discord.Interaction):
    entries = recall_notebook_entries(interaction.user, "", limit=500)
    ids = [e.get("id") for e in entries if e.get("kind") != "mirror" and e.get("id")]
    if not ids:
        await interaction.response.send_message("No facets to mirror yet. Drop something in the well first.", ephemeral=True)
        return
    mirror_text = f"Mirror of {len(ids)} facets"
    record = append_notebook_entry(interaction.user, "mirror", mirror_text)
    await interaction.response.send_message(f"Mirrored {len(ids)} facets. ID: `{record['id']}`", ephemeral=True)


@tree.command(name="wallet", description="Check your subscription and wallet status")
@require_tier(ROLE_SUPPORTER)
async def cmd_wallet(interaction: discord.Interaction):
    tier = get_user_tier(interaction.user)
    embed = discord.Embed(title="Lantern Wallet", color=0xf59e0b)
    embed.add_field(name="Tier", value=tier.title(), inline=True)
    embed.add_field(name="User", value=str(interaction.user), inline=True)
    embed.add_field(name="Notebook", value=notebook_path(notebook_user_id(interaction.user)).name, inline=False)
    embed.set_footer(text="Local ledger. No bank or crypto wallet.")
    await interaction.response.send_message(embed=embed, ephemeral=True)


@tree.command(name="odds", description="Kalshi paper trade confidence snapshot")
@require_tier(ROLE_SUPPORTER)
async def cmd_odds(interaction: discord.Interaction):
    text = format_odds(limit=5)
    if len(text) > 1900:
        text = text[:1897] + "..."
    await interaction.response.send_message(f"```{text}```", ephemeral=True)


@tree.command(name="talk", description="Talk to a persistent dream character (Fox, Tower)")
@app_commands.describe(character="Character name", message="What do you say?")
@require_tier(ROLE_SUPPORTER)
async def cmd_talk(interaction: discord.Interaction, character: str, message: str):
    if not COGNITIVE_AVAILABLE or not get_cognitive_journal:
        await interaction.response.send_message(
            "Cognitive Dream Journal not available. Check bot setup.", ephemeral=True
        )
        return
    journal = get_cognitive_journal()
    user_id = notebook_user_id(interaction.user)
    response = journal.talk(character, message, user_id=user_id)
    await interaction.response.send_message(response, ephemeral=True)


@tree.command(name="converge", description="Run convergence loop report")
@require_tier(ROLE_PILOT)
async def cmd_converge(interaction: discord.Interaction):
    await interaction.response.send_message("Convergence loop report requested. Check #queue-visibility for results.", ephemeral=True)


@tree.command(name="rag-status", description="Check RAG dollhouse intake status")
@require_tier(ROLE_PILOT)
async def cmd_rag_status(interaction: discord.Interaction):
    await interaction.response.send_message("RAG status: flat-rag-house is current. Use /queue for intake details.", ephemeral=True)


@tree.command(name="place", description="Save a place to your notebook")
@app_commands.describe(text="Describe the place")
@require_tier(ROLE_PILOT)
async def cmd_place(interaction: discord.Interaction, text: str):
    record = append_notebook_entry(interaction.user, "place", text)
    await interaction.response.send_message(f"Place saved. ID: `{record['id']}`", ephemeral=True)


@tree.command(name="character", description="Save a character to your notebook")
@app_commands.describe(text="Describe the character")
@require_tier(ROLE_PILOT)
async def cmd_character(interaction: discord.Interaction, text: str):
    record = append_notebook_entry(interaction.user, "character", text)
    await interaction.response.send_message(f"Character saved. ID: `{record['id']}`", ephemeral=True)


@tree.command(name="symbol", description="Save a symbol to your notebook")
@app_commands.describe(text="Describe the symbol")
@require_tier(ROLE_PILOT)
async def cmd_symbol(interaction: discord.Interaction, text: str):
    record = append_notebook_entry(interaction.user, "symbol", text)
    await interaction.response.send_message(f"Symbol saved. ID: `{record['id']}`", ephemeral=True)


@tree.command(name="dispatch", description="Dispatch agent fleet")
@require_tier(ROLE_FOUNDER)
async def cmd_dispatch(interaction: discord.Interaction):
    await interaction.response.send_message("Agent fleet dispatch signal sent. Held until operator confirmation.", ephemeral=True)


@tree.command(name="controls", description="Local controls status")
@require_tier(ROLE_FOUNDER)
async def cmd_controls(interaction: discord.Interaction):
    await interaction.response.send_message("Local controls: held. Require operator-machine auth proof.", ephemeral=True)


@tree.command(name="boot-check", description="Dual boot readiness check")
@require_tier(ROLE_FOUNDER)
async def cmd_boot_check(interaction: discord.Interaction):
    await interaction.response.send_message("Dual boot: held until physical operator action. Windows remains host.", ephemeral=True)


@tree.command(name="release-gate", description="v1.0.0 promotion gate check")
@require_tier(ROLE_FOUNDER)
async def cmd_release_gate(interaction: discord.Interaction):
    await interaction.response.send_message("v1.0.0 gate: held. No release without operator approval and evidence.", ephemeral=True)


# ── MCP Orchestrator Integration (Optional) ──

@tree.command(name="orchestrator", description="Check Lantern orchestrator status")
@require_tier(ROLE_PILOT)
async def cmd_orchestrator_status(interaction: discord.Interaction):
    """Query MCP server for orchestrator health."""
    if not MCP_AVAILABLE or not get_bridge:
        await interaction.response.send_message(
            " MCP bridge not available. Install with: `pip install aiohttp`",
            ephemeral=True
        )
        return

    await interaction.response.defer()
    bridge = get_bridge()
    status_data = await bridge.get_orchestrator_status()

    embed = discord.Embed(title="Lantern Orchestrator Status", color=0x0d9488)
    embed.description = bridge.format_status_embed(status_data)
    embed.add_field(name="Timestamp", value=status_data.get("timestamp", "N/A"), inline=False)
    embed.add_field(name="Endpoint", value=bridge.mcp_url, inline=True)

    if status_data.get("status") != "online":
        embed.color = 0xdc2626  # Red if offline

    embed.set_footer(text="Powered by Lantern Orchestrator MCP Bridge")
    await interaction.followup.send(embed=embed)


@tree.command(name="queue", description="Check Lantern task queue")
@require_tier(ROLE_PILOT)
async def cmd_queue_status(interaction: discord.Interaction):
    """Query MCP server for pending tasks."""
    if not MCP_AVAILABLE or not get_bridge:
        await interaction.response.send_message(
            " MCP bridge not available. Install with: `pip install aiohttp`",
            ephemeral=True
        )
        return

    await interaction.response.defer()
    bridge = get_bridge()
    queue_data = await bridge.get_queue_tasks(limit=10)

    embed = discord.Embed(title="Lantern Task Queue", color=0x2563eb)
    embed.description = bridge.format_queue_embed(queue_data)
    embed.add_field(name="Timestamp", value=queue_data.get("timestamp", "N/A"), inline=False)

    if queue_data.get("count", 0) == 0:
        embed.color = 0x059669  # Green if queue empty

    embed.set_footer(text="Powered by Lantern Orchestrator MCP Bridge")
    await interaction.followup.send(embed=embed)


# ── Lantern Media Commands ──

@tree.command(name="music", description="Show current music status")
async def cmd_music(interaction: discord.Interaction):
    """Show music status and available commands."""
    if not ARCHIVE_AVAILABLE:
        await interaction.response.send_message(
            "Media curator unavailable.",
            ephemeral=True
        )
        return

    curator = get_curator()
    current = curator.get_current_item()

    embed = discord.Embed(
        title="Lantern Music Status",
        description=current['title'] if current else "No music loaded",
        color=discord.Color.gold()
    )

    if current:
        if 'album' in current:
            embed.add_field(name="Album", value=current['album'], inline=True)
        if 'year' in current:
            embed.add_field(name="Year", value=str(current['year']), inline=True)

    embed.add_field(
        name="Available Commands",
        value="/art — show library\n/movies — show all media\n/notes — save to journal",
        inline=False
    )
    embed.set_footer(text="From Internet Archive • CC-licensed")

    await interaction.response.send_message(embed=embed)


@tree.command(name="art", description="Show available art, books, and media")
async def cmd_art(interaction: discord.Interaction):
    """List available media collections."""
    if not ARCHIVE_AVAILABLE:
        await interaction.response.send_message("Media curator unavailable.", ephemeral=True)
        return

    curator = get_curator()
    embed = curator.get_playlist_embed()
    await interaction.response.send_message(embed=embed)


@tree.command(name="notes", description="Add a note to the shared journal")
@app_commands.describe(content="Your note text")
async def cmd_notes(interaction: discord.Interaction, content: str):
    """Add a note to the dreamer notebook."""
    user_id = notebook_user_id(interaction.user)
    nb_path = notebook_path(user_id)

    nb_path.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "timestamp": now_utc(),
        "user": interaction.user.name,
        "content": content[:MAX_NOTEBOOK_TEXT_LENGTH]
    }

    with open(nb_path, "a") as f:
        f.write(json.dumps(entry) + "\n")

    await interaction.response.send_message("Note saved.", ephemeral=True)


@tree.command(name="movies", description="Show available movies and documentaries")
async def cmd_movies(interaction: discord.Interaction):
    """List media from public domain and CC-licensed collections."""
    if not ARCHIVE_AVAILABLE:
        await interaction.response.send_message("Media curator unavailable.", ephemeral=True)
        return

    curator = get_curator()
    embed = discord.Embed(
        title="Lantern Media Library",
        description="CC-licensed and public domain audio, books, and films from Internet Archive",
        color=discord.Color.gold()
    )

    items = curator.get_collection_items()
    playlist_text = "\n".join(
        f"{i+1}. {item['title']} ({item.get('year', '?')})"
        for i, item in enumerate(items[:10])
    )

    embed.add_field(
        name="Available Now",
        value=playlist_text or "Loading...",
        inline=False
    )
    embed.set_footer(text="From Internet Archive • CC-licensed + Public Domain")

    await interaction.response.send_message(embed=embed)


# ── Voice & Music Commands (Frank Sinatra in Lounge) ──

@tree.command(name="sing", description="🎵 Sing Frank Sinatra in your voice channel")
@app_commands.describe(song="Song name (leave blank for current)")
async def cmd_sing(interaction: discord.Interaction, song: Optional[str] = None):
    """Play Frank Sinatra from Internet Archive in voice channel"""
    if not VOICE_AVAILABLE or not get_voice_player or not get_sinatra:
        await interaction.response.send_message(
            "🎵 Voice playback unavailable. Check FFmpeg installation: `choco install ffmpeg`",
            ephemeral=True
        )
        return

    # Check if user is in a voice channel
    if not interaction.user.voice or not interaction.user.voice.channel:
        await interaction.response.send_message(
            "🎵 You must be in a voice channel to request a song.",
            ephemeral=True
        )
        return

    await interaction.response.defer()

    # Get Sinatra collection
    sinatra = get_sinatra()

    # Find song
    if song:
        song_key = song.lower().replace(" ", "_")
        song_info = sinatra.get_song_info(song_key)
        if not song_info:
            await interaction.followup.send(
                f"Song '{song}' not found. Use `/music` to see available songs.",
                ephemeral=True
            )
            return
        song_url = song_info["url"]
        song_title = song_info["title"]
    else:
        current_key = sinatra.get_current_song()
        song_info = sinatra.get_song_info(current_key)
        if not song_info:
            await interaction.followup.send("No songs available.", ephemeral=True)
            return
        song_url = song_info["url"]
        song_title = song_info["title"]

    # Join voice and play
    voice_player = get_voice_player(client)
    joined = await voice_player.join_voice_channel(interaction.user.voice.channel)

    if not joined:
        await interaction.followup.send("❌ Could not join voice channel.", ephemeral=True)
        return

    playing = await voice_player.play_song(song_url)

    if playing:
        embed = discord.Embed(
            title="🎵 Now Playing",
            description=f"**{song_title}** — Frank Sinatra",
            color=discord.Color.gold()
        )
        embed.add_field(
            name="Album",
            value=song_info.get("album", "Unknown"),
            inline=True
        )
        embed.add_field(
            name="Year",
            value=str(song_info.get("year", "?")),
            inline=True
        )
        embed.set_footer(text="From Internet Archive • CC-licensed + Public Domain")
        await interaction.followup.send(embed=embed)
    else:
        await interaction.followup.send(
            "❌ Could not play audio. Ensure FFmpeg is installed and working.",
            ephemeral=True
        )


@tree.command(name="nextsong", description="⏭️ Skip to next song in queue")
async def cmd_next_song(interaction: discord.Interaction):
    """Play next song in Sinatra collection"""
    if not VOICE_AVAILABLE or not get_sinatra:
        await interaction.response.send_message("Voice unavailable.", ephemeral=True)
        return

    sinatra = get_sinatra()
    next_key = sinatra.next_song()
    next_info = sinatra.get_song_info(next_key)

    if next_info:
        await interaction.response.send_message(
            f"⏭️ Up next: **{next_info['title']}** ({next_info['year']})"
        )
    else:
        await interaction.response.send_message("No songs in queue.", ephemeral=True)


@tree.command(name="stop", description="⏹️ Stop playback and leave voice")
async def cmd_stop(interaction: discord.Interaction):
    """Stop audio and disconnect from voice"""
    if not VOICE_AVAILABLE or not get_voice_player:
        await interaction.response.send_message("Voice unavailable.", ephemeral=True)
        return

    voice_player = get_voice_player()
    if voice_player:
        await voice_player.stop_playback()
        await voice_player.disconnect()
        await interaction.response.send_message("⏹️ Stopped. Left voice channel.")
    else:
        await interaction.response.send_message("Not connected.", ephemeral=True)


@tree.command(name="leave", description="👋 Leave voice channel")
async def cmd_leave(interaction: discord.Interaction):
    """Disconnect from voice channel"""
    if not VOICE_AVAILABLE or not get_voice_player:
        await interaction.response.send_message("Voice unavailable.", ephemeral=True)
        return

    voice_player = get_voice_player()
    if voice_player:
        await voice_player.disconnect()
        await interaction.response.send_message("👋 Left the lounge.")
    else:
        await interaction.response.send_message("Not connected.", ephemeral=True)


# ── Events ──

@client.event
async def on_ready():
    print(f"[READY] Logged in as {client.user} at {now_utc()}")
    # Initialize voice player
    if VOICE_AVAILABLE:
        voice_player = get_voice_player(client)
        print(f"[INFO] Voice player initialized")
    # Sync globally (no guild-specific permissions required for testing)
    synced = await tree.sync()
    print(f"[SYNC] Synced {len(synced)} slash commands globally")
    if GUILD_ID_INT:
        print(f"[INFO] GUILD_ID set to {GUILD_ID_INT} for context")


@client.event
async def on_member_join(member: discord.Member):
    """Welcome new members with tier info."""
    try:
        await member.send(
            f"Welcome to Lantern OS, {member.display_name}!\n\n"
            "Available commands:\n"
            "- `/status` — Health check\n"
            "- `/help` — List commands for your tier\n"
            "- `/subscribe` — Upgrade to Supporter or Pilot\n\n"
            "Public tier is free. Supporter ($20/mo) unlocks dreamer commands. Pilot ($200/mo) unlocks workspace commands."
        )
    except discord.Forbidden:
        pass


# ── Main ──

def main():
    print("[INFO] Starting Lantern OS Discord Bot v2...")
    print("[INFO] Slash commands + role gating + notebook integration.")
    print("[INFO] No secrets are printed. Stop with Ctrl+C.")
    client.run(TOKEN)


if __name__ == "__main__":
    main()
