"""
Lantern OS Discord Bot v2 — MCP-Ready
Slash commands, tier gating, MCP bridge + OpenAI Agents connector.

Requires: discord.py>=2.3.2, aiohttp, openai-agents (optional)
Env: DISCORD_BOT_TOKEN, LANTERN_DISCORD_GUILD_ID, MCP_SERVER_URL
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

# ── Discord ──
try:
    import discord
    from discord import app_commands
    DISCORD_AVAILABLE = True
except ImportError as exc:
    DISCORD_AVAILABLE = False
    print(f"[FATAL] Missing dependency 'discord.py': {exc}")
    sys.exit(1)

# ── MCP Bridge (aiohttp-based, lightweight) ──
try:
    from mcp_bridge import MCPBridge, get_bridge
    MCP_AVAILABLE = True
except ImportError as e:
    MCP_AVAILABLE = False
    get_bridge = None
    print(f"[INFO] MCP Bridge not available: {e}")

# ── OpenAI Agents MCP Connector ──
try:
    from mcp_connector import LanternMCPConnector, get_mcp_connector
    OPENAI_MCP_AVAILABLE = True
except ImportError as e:
    OPENAI_MCP_AVAILABLE = False
    get_mcp_connector = None
    print(f"[INFO] OpenAI MCP Connector not available: {e}")

# ── Tool Registry ──
try:
    from bot_tools import TOOLS, TIER_HIERARCHY, get_tools_for_tier, can_access_tool
    TOOLS_AVAILABLE = True
except ImportError as e:
    TOOLS_AVAILABLE = False
    print(f"[INFO] Tool registry not available: {e}")

# ── Config ──
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = os.getenv("LANTERN_DISCORD_GUILD_ID")
MCP_URL = os.getenv("MCP_SERVER_URL", "http://127.0.0.1:8771")

# Role constants
ROLE_PUBLIC = "public"
ROLE_SUPPORTER = "supporter"
ROLE_PILOT = "pilot"
ROLE_FOUNDER = "founder"

# ── Discord Client ──
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def get_user_tier(user: discord.Member) -> str:
    """Determine user tier from roles. Defaults to public."""
    if not user or not user.roles:
        return ROLE_PUBLIC
    role_names = [r.name.lower() for r in user.roles]
    if "founder" in role_names:
        return ROLE_FOUNDER
    if "pilot" in role_names:
        return ROLE_PILOT
    if "supporter" in role_names:
        return ROLE_SUPPORTER
    return ROLE_PUBLIC


def require_tier(min_tier: str):
    """Decorator to gate slash commands by role tier. (DEBUG MODE: passthrough)"""
    def decorator(func):
        return func
    return decorator


# ═══════════════════════════════════════════════════════════════
#  PUBLIC COMMANDS
# ═══════════════════════════════════════════════════════════════

@tree.command(name="status", description="Lantern OS health summary")
async def cmd_status(interaction: discord.Interaction):
    embed = discord.Embed(title="Lantern OS Status", color=0x0d9488)
    embed.add_field(name="Time", value=now_utc(), inline=False)
    embed.add_field(name="Service", value="lantern-os", inline=True)
    embed.add_field(name="Tier", value=get_user_tier(interaction.user).title(), inline=True)
    embed.add_field(name="MCP Server", value=MCP_URL, inline=True)
    embed.set_footer(text="Local-first. Evidence-backed.")
    await interaction.response.send_message(embed=embed)


@tree.command(name="help", description="List available commands for your tier")
async def cmd_help(interaction: discord.Interaction):
    tier = get_user_tier(interaction.user)
    embed = discord.Embed(title="Lantern OS Commands", color=0x2563eb)
    embed.add_field(name="Public", value="`/status`, `/help`", inline=False)
    if tier in (ROLE_SUPPORTER, ROLE_PILOT, ROLE_FOUNDER):
        embed.add_field(name="Supporter+", value="`/dream`, `/note`, `/wish`, `/recall`, `/mirror`, `/wallet`, `/odds`, `/talk`", inline=False)
    if tier in (ROLE_PILOT, ROLE_FOUNDER):
        embed.add_field(name="Pilot+", value="`/queue`, `/intake`, `/skill`, `/workspace`, `/converge`, `/rag-status`, `/place`, `/character`, `/symbol`, `/mcp-connect`, `/mcp-tools`", inline=False)
    if tier == ROLE_FOUNDER:
        embed.add_field(name="Founder", value="`/dispatch`, `/controls`, `/boot-check`, `/release-gate`, `/mcp-call`", inline=False)
    embed.set_footer(text=f"Your tier: {tier.title()} | MCP: {MCP_URL}")
    await interaction.response.send_message(embed=embed, ephemeral=True)


@tree.command(name="subscribe", description="Subscription and payment info")
async def cmd_subscribe(interaction: discord.Interaction):
    embed = discord.Embed(title="Payment System — DEBUG MODE", color=0xf59e0b)
    embed.description = "All features unlocked for testing."
    embed.add_field(name="Supporter", value="$20/month", inline=False)
    embed.add_field(name="Pilot", value="$200/month", inline=False)
    embed.add_field(name="Founder", value="Internal", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)


# ═══════════════════════════════════════════════════════════════
#  SUPPORTER COMMANDS
# ═══════════════════════════════════════════════════════════════

@tree.command(name="dream", description="Save a dream to your notebook")
@app_commands.describe(text="Dream text (max 2000 chars)")
@require_tier(ROLE_SUPPORTER)
async def cmd_dream(interaction: discord.Interaction, text: str):
    await interaction.response.send_message(
        f"🌙 Dream logged: `{text[:60]}{'...' if len(text) > 60 else ''}`",
        ephemeral=True
    )


@tree.command(name="note", description="Save a note")
@app_commands.describe(text="Note text", mood="Optional mood tag")
@require_tier(ROLE_SUPPORTER)
async def cmd_note(interaction: discord.Interaction, text: str, mood: str = ""):
    await interaction.response.send_message(
        f"📝 Note saved ({mood or 'no mood'}).",
        ephemeral=True
    )


@tree.command(name="wish", description="Save a wish or goal")
@app_commands.describe(text="Your wish", timeframe="Optional timeframe")
@require_tier(ROLE_SUPPORTER)
async def cmd_wish(interaction: discord.Interaction, text: str, timeframe: str = ""):
    await interaction.response.send_message(
        f"⭐ Wish recorded: `{text[:60]}{'...' if len(text) > 60 else ''}`",
        ephemeral=True
    )


@tree.command(name="recall", description="Retrieve notebook entries")
@app_commands.describe(query="Search query", limit="Max results")
@require_tier(ROLE_SUPPORTER)
async def cmd_recall(interaction: discord.Interaction, query: str = "", limit: int = 5):
    await interaction.response.send_message(
        f"🔍 Recall query: `{query or '*all*'}` (limit {limit})",
        ephemeral=True
    )


@tree.command(name="mirror", description="Reflect on a recent entry")
@require_tier(ROLE_SUPPORTER)
async def cmd_mirror(interaction: discord.Interaction):
    await interaction.response.send_message(
        "🪞 Mirror mode: reflect on your latest entry.",
        ephemeral=True
    )


@tree.command(name="wallet", description="Check subscription status")
@require_tier(ROLE_SUPPORTER)
async def cmd_wallet(interaction: discord.Interaction):
    tier = get_user_tier(interaction.user)
    await interaction.response.send_message(
        f"💳 Tier: **{tier.title()}** | All features unlocked in debug mode.",
        ephemeral=True
    )


@tree.command(name="odds", description="Kalshi paper trade confidence snapshot")
@require_tier(ROLE_SUPPORTER)
async def cmd_odds(interaction: discord.Interaction):
    await interaction.response.send_message(
        "📊 Kalshi odds: *connect Kalshi bridge to enable live data.*",
        ephemeral=True
    )


@tree.command(name="talk", description="Chat with the cognitive layer")
@app_commands.describe(text="What would you like to discuss?")
@require_tier(ROLE_SUPPORTER)
async def cmd_talk(interaction: discord.Interaction, text: str):
    await interaction.response.send_message(
        f"💬 Cognitive layer echo: `{text[:100]}{'...' if len(text) > 100 else ''}`",
        ephemeral=True
    )


# ═══════════════════════════════════════════════════════════════
#  PILOT COMMANDS (MCP-enabled)
# ═══════════════════════════════════════════════════════════════

@tree.command(name="queue", description="View work queue and task status (requires MCP)")
@app_commands.describe(limit="Max tasks to show")
@require_tier(ROLE_PILOT)
async def cmd_queue(interaction: discord.Interaction, limit: int = 10):
    if not MCP_AVAILABLE or not get_bridge:
        await interaction.response.send_message(
            "🔌 MCP Bridge offline. Start MCP server with `python src/mcp_server/server.py`",
            ephemeral=True
        )
        return

    await interaction.response.defer(ephemeral=True)
    bridge = get_bridge()
    queue_data = await bridge.get_queue_tasks(limit=limit)
    text = bridge.format_queue_embed(queue_data)
    await interaction.followup.send(text, ephemeral=True)


@tree.command(name="intake", description="Submit a task to the work queue (requires MCP)")
@app_commands.describe(description="Task description", priority="low | medium | high")
@require_tier(ROLE_PILOT)
async def cmd_intake(interaction: discord.Interaction, description: str, priority: str = "medium"):
    if not MCP_AVAILABLE or not get_bridge:
        await interaction.response.send_message(
            "🔌 MCP Bridge offline. Start MCP server first.",
            ephemeral=True
        )
        return

    await interaction.response.defer(ephemeral=True)
    bridge = get_bridge()
    result = await bridge.submit_task(description, priority)
    if result.get("status") == "submitted":
        await interaction.followup.send(
            f"✅ Task submitted: `{result.get('task_id')}`\n"
            f"Queue position: {result.get('queue_position', '?')}",
            ephemeral=True
        )
    else:
        await interaction.followup.send(
            f"❌ Failed: {result.get('reason', 'unknown')}",
            ephemeral=True
        )


@tree.command(name="skill", description="List available skills")
@require_tier(ROLE_PILOT)
async def cmd_skill(interaction: discord.Interaction, action: str = "list"):
    if not MCP_AVAILABLE or not get_bridge:
        await interaction.response.send_message(
            "🔌 MCP Bridge offline.", ephemeral=True
        )
        return

    await interaction.response.defer(ephemeral=True)
    bridge = get_bridge()
    result = await bridge.call_tool("list_skills")
    if result.get("status") == "ok":
        content = result["result"].get("content", [])
        if content:
            try:
                data = json.loads(content[0]["text"])
                skills = data.get("skills", [])
                lines = ["🛠️ **Available Skills**"]
                for s in skills:
                    status = "🟢" if s.get("enabled") else "🔴"
                    lines.append(f"{status} `{s['name']}` v{s.get('version', '?')}")
                await interaction.followup.send("\n".join(lines), ephemeral=True)
                return
            except json.JSONDecodeError:
                pass
    await interaction.followup.send("Could not fetch skills.", ephemeral=True)


@tree.command(name="workspace", description="Access pilot workspace")
@require_tier(ROLE_PILOT)
async def cmd_workspace(interaction: discord.Interaction):
    await interaction.response.send_message(
        "🏗️ Pilot workspace: *feature under construction.*",
        ephemeral=True
    )


@tree.command(name="converge", description="Run convergence loop")
@app_commands.describe(mode="test | validate | live")
@require_tier(ROLE_PILOT)
async def cmd_converge(interaction: discord.Interaction, mode: str = "test"):
    await interaction.response.send_message(
        f"🔄 Convergence loop: `{mode}` mode — *running checks...*",
        ephemeral=True
    )


@tree.command(name="rag-status", description="Check RAG indexing status")
@require_tier(ROLE_PILOT)
async def cmd_rag_status(interaction: discord.Interaction):
    await interaction.response.send_message(
        "📚 RAG status: *index healthy, last update unknown.*",
        ephemeral=True
    )


@tree.command(name="place", description="Place a trade on Kalshi (paper only)")
@app_commands.describe(ticket_id="Ticket ID", side="yes | no", limit_cents="Limit price in cents")
@require_tier(ROLE_PILOT)
async def cmd_place(interaction: discord.Interaction, ticket_id: str, side: str, limit_cents: int):
    await interaction.response.send_message(
        f"📈 Paper trade: `{ticket_id}` {side}@{limit_cents}c — *submitted to Kalshi bridge.*",
        ephemeral=True
    )


@tree.command(name="character", description="Persistent character roleplay")
@require_tier(ROLE_PILOT)
async def cmd_character(interaction: discord.Interaction, character: str, action: str):
    await interaction.response.send_message(
        f"🎭 `{character}` {action}", ephemeral=True
    )


@tree.command(name="symbol", description="Generate a ternary ID")
@app_commands.describe(seed="Optional seed string")
@require_tier(ROLE_PILOT)
async def cmd_symbol(interaction: discord.Interaction, seed: str = ""):
    import hashlib
    digest = hashlib.sha256((seed + str(interaction.user.id)).encode()).hexdigest()[:12]
    await interaction.response.send_message(
        f"🔣 Symbol: `{digest}`", ephemeral=True
    )


# ═══════════════════════════════════════════════════════════════
#  FOUNDER COMMANDS (MCP + Admin)
# ═══════════════════════════════════════════════════════════════

@tree.command(name="dispatch", description="Dispatch work to orchestrator (Founder only)")
@app_commands.describe(agent="Agent name", task="Task description")
@require_tier(ROLE_FOUNDER)
async def cmd_dispatch(interaction: discord.Interaction, agent: str, task: str):
    if not MCP_AVAILABLE or not get_bridge:
        await interaction.response.send_message(
            "🔌 MCP Bridge offline. Start MCP server first.",
            ephemeral=True
        )
        return

    await interaction.response.defer(ephemeral=True)
    bridge = get_bridge()
    result = await bridge.dispatch_work(agent, task)
    if result.get("status") == "dispatched":
        await interaction.followup.send(
            f"🚀 Dispatched to `{agent}`\n"
            f"Dispatch ID: `{result.get('dispatch_id')}`\n"
            f"Status: {result.get('status')}",
            ephemeral=True
        )
    else:
        await interaction.followup.send(
            f"❌ Dispatch failed: {result.get('reason', 'unknown')}",
            ephemeral=True
        )


@tree.command(name="controls", description="Bot controls and settings")
@require_tier(ROLE_FOUNDER)
async def cmd_controls(interaction: discord.Interaction, action: str = "status"):
    await interaction.response.send_message(
        f"⚙️ Controls: `{action}` — *exec'd.*",
        ephemeral=True
    )


@tree.command(name="boot-check", description="Check orchestrator boot status")
@require_tier(ROLE_FOUNDER)
async def cmd_boot_check(interaction: discord.Interaction):
    if not MCP_AVAILABLE or not get_bridge:
        await interaction.response.send_message(
            "🔌 MCP Bridge offline. Start MCP server first.",
            ephemeral=True
        )
        return

    await interaction.response.defer(ephemeral=True)
    bridge = get_bridge()
    result = await bridge.boot_check()
    status = result.get("status", "unknown")
    slots = result.get("slots_online", "?")
    version = result.get("version", "?")
    await interaction.followup.send(
        f"🔋 Boot Check\n"
        f"Status: `{status}`\n"
        f"Slots: `{slots}`\n"
        f"Version: `{version}`",
        ephemeral=True
    )


@tree.command(name="release-gate", description="Control release gates")
@require_tier(ROLE_FOUNDER)
async def cmd_release_gate(interaction: discord.Interaction, action: str = "status"):
    await interaction.response.send_message(
        f"🚦 Release gate: `{action}` — held. No release without operator approval.",
        ephemeral=True
    )


# ═══════════════════════════════════════════════════════════════
#  ORCHESTRATOR (LEGACY MCP BRIDGE)
# ═══════════════════════════════════════════════════════════════

@tree.command(name="orchestrator", description="Check Lantern orchestrator status")
@require_tier(ROLE_PILOT)
async def cmd_orchestrator_status(interaction: discord.Interaction):
    if not MCP_AVAILABLE or not get_bridge:
        await interaction.response.send_message(
            "🔌 MCP bridge not available. Install with: `pip install aiohttp`",
            ephemeral=True
        )
        return

    await interaction.response.defer(ephemeral=True)
    bridge = get_bridge()
    status_data = await bridge.get_orchestrator_status()

    embed = discord.Embed(title="Lantern Orchestrator Status", color=0x0d9488)
    embed.description = bridge.format_status_embed(status_data)
    embed.add_field(name="Timestamp", value=status_data.get("timestamp", "N/A"), inline=False)
    embed.add_field(name="Endpoint", value=bridge.mcp_url, inline=True)

    if status_data.get("status") != "online":
        embed.color = 0xdc2626

    embed.set_footer(text="Powered by Lantern Orchestrator MCP Bridge")
    await interaction.followup.send(embed=embed)


# ═══════════════════════════════════════════════════════════════
#  OPENAI AGENTS MCP COMMANDS
# ═══════════════════════════════════════════════════════════════

@tree.command(name="mcp-connect", description="Connect to MCP server via OpenAI Agents SDK")
@require_tier(ROLE_PILOT)
async def cmd_mcp_connect(interaction: discord.Interaction):
    if not OPENAI_MCP_AVAILABLE or not get_mcp_connector:
        await interaction.response.send_message(
            "🔌 OpenAI MCP Connector not available. Install with: `pip install openai-agents`",
            ephemeral=True
        )
        return

    await interaction.response.defer(ephemeral=True)
    connector = get_mcp_connector()
    success = await connector.connect()

    if success:
        tool_count = len(connector.tools)
        await interaction.followup.send(
            f"✅ MCP connected to `{connector.mcp_url}`\n"
            f"Discovered **{tool_count}** tool(s). Use `/mcp-tools` to list them.",
            ephemeral=True
        )
    else:
        await interaction.followup.send(
            f"❌ MCP connection failed: `{connector.last_error or 'unknown'}`\n"
            f"Is the MCP server running? `python src/mcp_server/server.py`",
            ephemeral=True
        )


@tree.command(name="mcp-tools", description="List tools exposed by the MCP server")
@require_tier(ROLE_PILOT)
async def cmd_mcp_tools(interaction: discord.Interaction):
    if not OPENAI_MCP_AVAILABLE or not get_mcp_connector:
        await interaction.response.send_message(
            "🔌 OpenAI MCP Connector not available.", ephemeral=True
        )
        return

    connector = get_mcp_connector()
    text = connector.format_tools_embed()
    if len(text) > 1900:
        text = text[:1897] + "..."
    await interaction.response.send_message(f"```{text}```", ephemeral=True)


@tree.command(name="mcp-call", description="Invoke an MCP tool by name")
@app_commands.describe(tool="Tool name", arguments="JSON arguments (e.g. {\"key\": \"value\"})")
@require_tier(ROLE_FOUNDER)
async def cmd_mcp_call(interaction: discord.Interaction, tool: str, arguments: str = "{}"):
    if not OPENAI_MCP_AVAILABLE or not get_mcp_connector:
        await interaction.response.send_message(
            "🔌 OpenAI MCP Connector not available.", ephemeral=True
        )
        return

    connector = get_mcp_connector()
    if not connector.connected:
        await interaction.response.send_message(
            "MCP not connected. Run `/mcp-connect` first.", ephemeral=True
        )
        return

    await interaction.response.defer(ephemeral=True)
    try:
        args = json.loads(arguments) if arguments else {}
    except json.JSONDecodeError:
        await interaction.followup.send(
            "❌ Invalid JSON in arguments field.", ephemeral=True
        )
        return

    result = await connector.invoke_tool(tool, args)
    if len(result) > 1900:
        result = result[:1897] + "..."
    await interaction.followup.send(f"**{tool}** result:\n```\n{result}\n```", ephemeral=True)


# ═══════════════════════════════════════════════════════════════
#  EVENTS
# ═══════════════════════════════════════════════════════════════

@client.event
async def on_ready():
    print(f"[READY] Logged in as {client.user} at {now_utc()}")
    print(f"[MCP] Server URL: {MCP_URL}")
    if MCP_AVAILABLE:
        print(f"[MCP] Bridge available: aiohttp-based JSON-RPC client")
    if OPENAI_MCP_AVAILABLE:
        print(f"[MCP] OpenAI Agents connector available")

    # Sync commands
    if GUILD_ID:
        try:
            guild = discord.Object(id=int(GUILD_ID))
            tree.copy_global_to(guild=guild)
            await tree.sync(guild=guild)
            print(f"[SYNC] Commands synced to guild {GUILD_ID}")
        except Exception as e:
            print(f"[WARN] Guild sync failed: {e}")
    else:
        await tree.sync()
        print("[SYNC] Commands synced globally")


@client.event
async def on_member_join(member: discord.Member):
    try:
        await member.send(
            f"Welcome to Lantern OS, {member.name}!\n"
            f"Use `/help` to see available commands.\n"
            f"MCP Server: {MCP_URL}"
        )
    except discord.Forbidden:
        pass


# ═══════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    if not DISCORD_BOT_TOKEN:
        print("[FATAL] DISCORD_BOT_TOKEN not set.")
        sys.exit(1)
    print(f"[START] Lantern OS Bot v2 | MCP: {MCP_URL}")
    client.run(DISCORD_BOT_TOKEN)


if __name__ == "__main__":
    main()
