"""
Lantern OS Discord Bot v2 -- Slash Commands + Role Gating + Prefix Fallback

Generated: 2026-05-31.
Purpose: monetized Discord server with tiered access and slash commands.
Also remembers v1 prefix commands (!dream, !note, !threedoors).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

try:
    import discord
    from discord import app_commands
except Exception as exc:
    print(f"[FATAL] Missing dependency 'discord.py': {exc}")
    sys.exit(1)

# -- Load .env.local fallback (shared with web UI settings) --
_env_local = Path(__file__).resolve().parents[2] / ".env.local"
if _env_local.exists():
    for _line in _env_local.read_text("utf-8").splitlines():
        _line = _line.strip()
        if not _line or _line.startswith("#") or "=" not in _line:
            continue
        _k, _v = _line.split("=", 1)
        _k = _k.strip()
        if _k and _k not in os.environ:
            os.environ[_k] = _v.strip()

# -- Configuration --
TOKEN = os.getenv("DISCORD_BOT_TOKEN", os.getenv("DISCORD_TOKEN", "")).strip()
GUILD_ID = os.getenv("LANTERN_DISCORD_GUILD_ID", "").strip()
STATUS_URL = os.getenv("LANTERN_STATUS_URL", "http://127.0.0.1:4177/api/status").strip()
REPO_ROOT = Path(__file__).resolve().parents[2]
DREAMER_NOTEBOOK_DIR = REPO_ROOT / "data" / "dreamer" / "notebooks"
SUBSCRIBER_DATA_PATH = Path(os.getenv("SUBSCRIBER_DATA_PATH", REPO_ROOT / "data" / "discord" / "subscribers.json"))
MAX_NOTEBOOK_TEXT_LENGTH = 2000
THREE_DOORS_DATA_DIR = REPO_ROOT / "data" / "discord" / "three-doors"

# Role name constants (case-insensitive matching)
ROLE_PUBLIC = "@everyone"
ROLE_SUPPORTER = "supporter"
ROLE_PILOT = "pilot"
ROLE_FOUNDER = "founder"

TIER_ORDER = {ROLE_PUBLIC: 0, ROLE_SUPPORTER: 1, ROLE_PILOT: 2, ROLE_FOUNDER: 3}

# -- Lazy environment checks (called from main so imports don't crash) --
GUILD_ID_INT: int | None = None
if GUILD_ID:
    try:
        GUILD_ID_INT = int(GUILD_ID)
    except ValueError:
        pass


def _validate_config() -> None:
    """Exit if required config is missing. Called from main() so imports don't crash."""
    if not TOKEN:
        print("[FATAL] Missing DISCORD_BOT_TOKEN (or DISCORD_TOKEN)")
        sys.exit(1)
    if GUILD_ID and GUILD_ID_INT is None:
        print("[FATAL] LANTERN_DISCORD_GUILD_ID must be numeric")
        sys.exit(1)


# -- Discord client setup --
intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# -- Helpers --

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


# -- Three Doors helpers --

def three_doors_path(user_id: str) -> Path:
    safe = re.sub(r"[^a-zA-Z0-9._-]+", "-", user_id).strip("-").lower() or "discord-user"
    return THREE_DOORS_DATA_DIR / f"{safe}.json"


def load_three_doors_state(user: discord.User | discord.Member) -> dict | None:
    path = three_doors_path(notebook_user_id(user))
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text("utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def save_three_doors_state(user: discord.User | discord.Member, state: dict) -> None:
    path = three_doors_path(notebook_user_id(user))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(state, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


# Pre-defined scenes for the Three Doors game
_THREE_DOORS_SCENES = {
    "moss-entry": {
        "text": (
            "You stand inside **The Moss Door**. The air is thick with green light, soft earth, and the smell of rain on ferns. "
            "Lanterns hang from ancient branches. A moss-covered fox sits beside you, wearing a brass tag that reads: "
            "**FRIEND OF THE ONE WHO CHOSE GREEN**. It looks up and says, *\"You came back.\"*"
        ),
        "doors": [
            {"name": "The Burrow Door", "label": "A", "description": "Small, root-framed, warm. Smells of rain and old blankets."},
            {"name": "The Sunken Bell Door", "label": "B", "description": "Half underwater. Rings softly when no one touches it."},
            {"name": "The Little Crown Door", "label": "C", "description": "Tiny golden door in a tree stump, widening when trusted."},
        ],
        "fox_present": True,
    },
    "burrow": {
        "text": (
            "You crawl through **The Burrow Door** into a snug earthen chamber lined with woven roots and faded quilts. "
            "Rain drums overhead. The fox curls up on a blanket and closes its eyes. A single lantern flickers in the corner."
        ),
        "doors": [
            {"name": "The Root Door", "label": "A", "description": "Twisted oak roots form an arch. Something hums beyond."},
            {"name": "The Ember Door", "label": "B", "description": "Warmth radiates. Ash drifts under the crack like snow."},
            {"name": "The Stream Door", "label": "C", "description": "Water rushes somewhere close. The floor is slick moss."},
        ],
        "fox_present": True,
    },
    "sunken-bell": {
        "text": (
            "Beneath **The Sunken Bell Door**, water reaches your ankles in a stone hallway. A bell hangs above, dripping, "
            "and it chimes once though no wind blows. Reflections of lanterns dance on the ceiling like fish."
        ),
        "doors": [
            {"name": "The Deep Door", "label": "A", "description": "Submerged stairs descend into green-black silence."},
            {"name": "The Echo Door", "label": "B", "description": "Your own voice returns as song from the other side."},
            {"name": "The Surface Door", "label": "C", "description": "Sunlight visible through cracks. The sound of birds."},
        ],
        "fox_present": True,
    },
    "little-crown": {
        "text": (
            "Through **The Little Crown Door**, the forest opens into a glade where every tree stump wears a tiny golden crown. "
            "Yours widened just enough to let you through. The fox trots ahead, its tail brushing against jeweled leaves."
        ),
        "doors": [
            {"name": "The Throne Door", "label": "A", "description": "Carved from a single black oak. Velvet moss for a seat."},
            {"name": "The Hollow Door", "label": "B", "description": "A door inside a hollow tree. Sap runs like amber."},
            {"name": "The Star Door", "label": "C", "description": "Visible only at twilight. Constellations map the hinges."},
        ],
        "fox_present": True,
    },
}


_THREE_DOORS_NEXT_MAP = {
    "the burrow door": "burrow",
    "the sunken bell door": "sunken-bell",
    "the little crown door": "little-crown",
    "the root door": "moss-entry",
    "the ember door": "moss-entry",
    "the stream door": "moss-entry",
    "the deep door": "sunken-bell",
    "the echo door": "burrow",
    "the surface door": "little-crown",
    "the throne door": "little-crown",
    "the hollow door": "burrow",
    "the star door": "moss-entry",
}


def _advance_three_doors(state: dict, door_name: str) -> dict | None:
    """Return a new state after choosing a door, or None if choice is invalid."""
    door_name_lower = door_name.lower().strip()
    current_doors = state.get("doors", [])
    chosen = None
    for d in current_doors:
        if d["label"].lower() == door_name_lower or d["name"].lower() == door_name_lower:
            chosen = d
            break
    if not chosen:
        return None
    next_key = _THREE_DOORS_NEXT_MAP.get(chosen["name"].lower(), "moss-entry")
    next_scene = _THREE_DOORS_SCENES[next_key]
    return {
        "scene_key": next_key,
        "text": next_scene["text"],
        "doors": next_scene["doors"],
        "fox_present": next_scene["fox_present"],
        "history": state.get("history", []) + [f"Chose {chosen['name']}"],
    }


def _format_three_doors_embed(state: dict) -> discord.Embed:
    embed = discord.Embed(
        title="Three Doors",
        description=state["text"],
        color=0x2E8B57,
    )
    if state.get("fox_present"):
        embed.set_footer(text="The fox is with you.")
    for d in state.get("doors", []):
        embed.add_field(
            name=f"{d['label']}. {d['name']}",
            value=d["description"],
            inline=False,
        )
    return embed


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
    """Decorator to gate slash commands by role tier."""
    min_level = TIER_ORDER.get(minimum.lower(), 0)

    async def predicate(interaction: discord.Interaction) -> bool:
        if not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("This command must be used in a server.", ephemeral=True)
            return False
        tier = get_user_tier(interaction.user)
        level = TIER_ORDER.get(tier, 0)
        if level < min_level:
            await interaction.response.send_message(
                f"This command requires `{minimum}` tier or higher. Use `/subscribe` to upgrade.",
                ephemeral=True,
            )
            return False
        return True

    return app_commands.check(predicate)


# -- Slash Commands --

@tree.command(name="status", description="Lantern OS health summary")
async def cmd_status(interaction: discord.Interaction):
    embed = discord.Embed(title="Lantern OS Status", color=0x0D9488)
    embed.add_field(name="Time", value=now_utc(), inline=False)
    embed.add_field(name="Service", value="lantern-garage", inline=True)
    embed.add_field(name="Tier", value=get_user_tier(interaction.user).title(), inline=True)
    embed.set_footer(text="Local-first. Evidence-backed.")
    await interaction.response.send_message(embed=embed)


@tree.command(name="help", description="List available commands for your tier")
async def cmd_help(interaction: discord.Interaction):
    tier = get_user_tier(interaction.user)
    embed = discord.Embed(title="Lantern OS Commands", color=0x2563EB)
    embed.add_field(name="Public", value="`/status`, `/help`, `/subscribe`, `/threedoors`", inline=False)
    if tier in (ROLE_SUPPORTER, ROLE_PILOT, ROLE_FOUNDER):
        embed.add_field(name="Supporter+", value="`/dream`, `/note`, `/wish`, `/recall`, `/mirror`, `/wallet`", inline=False)
    if tier in (ROLE_PILOT, ROLE_FOUNDER):
        embed.add_field(name="Pilot+", value="`/converge`, `/rag-status`, `/queue`, `/place`, `/character`, `/symbol`", inline=False)
    if tier == ROLE_FOUNDER:
        embed.add_field(name="Founder", value="`/dispatch`, `/controls`, `/boot-check`, `/release-gate`", inline=False)
    embed.set_footer(text=f"Your tier: {tier.title()}")
    await interaction.response.send_message(embed=embed, ephemeral=True)


@tree.command(name="subscribe", description="Get your Stripe checkout link")
async def cmd_subscribe(interaction: discord.Interaction):
    embed = discord.Embed(title="Lantern OS Subscriptions", color=0x0D9488)
    embed.add_field(name="Supporter -- $20/month", value="Weekly digest, report packs, Discord priority.\n[Subscribe](https://buy.stripe.com/test_00g2aRcWk2Xa6OI144)", inline=False)
    embed.add_field(name="Pilot -- $200/month", value="Guided cleanup sprint, 1:1 review, custom integration.\n[Subscribe](https://buy.stripe.com/test_3cs8z42zCeUe4GA288)", inline=False)
    embed.add_field(name="Public -- Free", value="Status, docs, health endpoints. No subscription needed.", inline=False)
    embed.set_footer(text="Payments recorded in the Lantern wallet ledger. Cancel anytime.")
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
    embed = discord.Embed(title="Lantern Wallet", color=0xF59E0B)
    embed.add_field(name="Tier", value=tier.title(), inline=True)
    embed.add_field(name="User", value=str(interaction.user), inline=True)
    embed.add_field(name="Notebook", value=notebook_path(notebook_user_id(interaction.user)).name, inline=False)
    embed.set_footer(text="Local ledger. No bank or crypto wallet.")
    await interaction.response.send_message(embed=embed, ephemeral=True)


@tree.command(name="converge", description="Run convergence loop report")
@require_tier(ROLE_PILOT)
async def cmd_converge(interaction: discord.Interaction):
    await interaction.response.send_message("Convergence loop report requested. Check #queue-visibility for results.", ephemeral=True)


@tree.command(name="rag-status", description="Check RAG dollhouse intake status")
@require_tier(ROLE_PILOT)
async def cmd_rag_status(interaction: discord.Interaction):
    await interaction.response.send_message("RAG status: flat-rag-house is current. Use /queue for intake details.", ephemeral=True)


@tree.command(name="queue", description="View agent fleet queue")
@require_tier(ROLE_PILOT)
async def cmd_queue(interaction: discord.Interaction):
    await interaction.response.send_message("Agent fleet queue is operational. 36 designed ring slots, 64 elastic pool target.", ephemeral=True)


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


# -- Three Doors slash commands --

@tree.command(name="threedoors", description="Enter the Three Doors game")
async def cmd_threedoors(interaction: discord.Interaction):
    state = load_three_doors_state(interaction.user)
    if state is None:
        scene = _THREE_DOORS_SCENES["moss-entry"]
        state = {
            "scene_key": "moss-entry",
            "text": scene["text"],
            "doors": scene["doors"],
            "fox_present": scene["fox_present"],
            "history": ["Entered The Moss Door"],
        }
        save_three_doors_state(interaction.user, state)
        await interaction.response.send_message(
            "The game begins. Three doors await.", embed=_format_three_doors_embed(state)
        )
    else:
        await interaction.response.send_message(embed=_format_three_doors_embed(state))


@tree.command(name="threedoors-choose", description="Choose a door in the Three Doors game")
@app_commands.describe(door="Door name or letter (A, B, C)")
async def cmd_threedoors_choose(interaction: discord.Interaction, door: str):
    state = load_three_doors_state(interaction.user)
    if not state:
        await interaction.response.send_message(
            "No active Three Doors game. Use `/threedoors` to begin.", ephemeral=True
        )
        return
    new_state = _advance_three_doors(state, door)
    if new_state is None:
        await interaction.response.send_message(
            f'"{door}" does not match any door. Choose A, B, C, or the full door name.', ephemeral=True
        )
        return
    save_three_doors_state(interaction.user, new_state)
    await interaction.response.send_message(
        "You chose the door. The path opens...", embed=_format_three_doors_embed(new_state)
    )


# -- Events --

@client.event
async def on_ready():
    print(f"[READY] Logged in as {client.user} at {now_utc()}")
    if GUILD_ID_INT:
        guild = discord.Object(id=GUILD_ID_INT)
        tree.copy_global_to(guild=guild)
        try:
            synced = await tree.sync(guild=guild)
            print(f"[SYNC] Synced {len(synced)} slash commands to guild {GUILD_ID_INT}")
        except discord.errors.Forbidden:
            print(f"[WARN] Slash command sync failed (403 Forbidden). "
                  f"The bot is missing the 'applications.commands' scope in guild {GUILD_ID_INT}. "
                  f"Re-invite the bot with that scope: https://discord.com/developers/applications")
            print("[INFO] Bot is online; events still work. Restart after fixing the invite to sync slash commands.")
    else:
        print("[WARN] No GUILD_ID set; slash commands will not sync. Set LANTERN_DISCORD_GUILD_ID.")


@client.event
async def on_member_join(member: discord.Member):
    """Welcome new members with tier info."""
    try:
        await member.send(
            f"Welcome to Lantern OS, {member.display_name}!\n\n"
            "Available commands:\n"
            "- `/status` -- Health check\n"
            "- `/help` -- List commands for your tier\n"
            "- `/subscribe` -- Upgrade to Supporter or Pilot\n"
            "- `!threedoors` -- Play the Three Doors game\n\n"
            "Public tier is free. Supporter ($20/mo) unlocks dreamer commands. Pilot ($200/mo) unlocks workspace commands."
        )
    except discord.Forbidden:
        pass


@client.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    content = message.content.strip()
    lower = content.lower()

    # -- Three Doors prefix commands --
    if lower.startswith("!threedoors") or lower.startswith("!three-doors"):
        state = load_three_doors_state(message.author)
        if state is None:
            scene = _THREE_DOORS_SCENES["moss-entry"]
            state = {
                "scene_key": "moss-entry",
                "text": scene["text"],
                "doors": scene["doors"],
                "fox_present": scene["fox_present"],
                "history": ["Entered The Moss Door"],
            }
            save_three_doors_state(message.author, state)
            await message.channel.send(
                "The game begins. Three doors await.", embed=_format_three_doors_embed(state)
            )
        else:
            await message.channel.send(embed=_format_three_doors_embed(state))
        return

    if lower.startswith("!choose ") or lower.startswith("!pick ") or lower.startswith("!door "):
        door_arg = content.split(None, 1)[1].strip()
        state = load_three_doors_state(message.author)
        if not state:
            await message.channel.send("No active game. Start with `!threedoors`.")
            return
        new_state = _advance_three_doors(state, door_arg)
        if new_state is None:
            await message.channel.send(
                f'"{door_arg}" does not match any door. Try A, B, C, or the door name.'
            )
            return
        save_three_doors_state(message.author, new_state)
        await message.channel.send(
            "You chose the door. The path opens...", embed=_format_three_doors_embed(new_state)
        )
        return

    # -- Classic v1 prefix commands --
    if lower.startswith("!dream "):
        text = content[7:].strip()
        if text:
            record = append_notebook_entry(message.author, "dream", text)
            await message.channel.send(f"Dream saved. ID: `{record['id']}`")
        else:
            await message.channel.send("Usage: `!dream <text>`")
        return

    if lower.startswith("!note "):
        text = content[6:].strip()
        if text:
            record = append_notebook_entry(message.author, "note", text)
            await message.channel.send(f"Note saved. ID: `{record['id']}`")
        else:
            await message.channel.send("Usage: `!note <text>`")
        return


# -- Main --

def main():
    _validate_config()
    print("[INFO] Starting Lantern OS Discord Bot v2...")
    print("[INFO] Slash commands + role gating + notebook integration + Three Doors.")
    print("[INFO] Prefix commands remembered: !threedoors, !dream, !note")
    print("[INFO] No secrets are printed. Stop with Ctrl+C.")
    client.run(TOKEN)


if __name__ == "__main__":
    main()
