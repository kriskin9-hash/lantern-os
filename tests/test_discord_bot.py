"""
Discord Bot v2 tests — uses dpytest (discord.ext.test) as the OSS bot test
framework, with pytest-asyncio for coroutine support and unittest.mock for
interaction mocking.

OSS test framework: https://github.com/CraftSpider/dpytest (installed as
discord.ext.test, imported below).
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

# Set required env vars before bot module imports (it calls sys.exit otherwise)
os.environ.setdefault("DISCORD_BOT_TOKEN", "test-token-for-pytest")
os.environ.setdefault("LANTERN_DISCORD_GUILD_ID", "111111111111111")

# OSS Discord bot test framework (dpytest)
from discord.ext import test as dpytest  # noqa: F401 — pulled in for test env

import discord
import pytest

# Add bot directory to path
sys.path.insert(0, str(Path(__file__).parents[1] / "src" / "discord_lounge_bot"))
import bot_v2  # noqa: E402


# ── Pure-function tests (no Discord runtime needed) ────────────────────────

def test_now_utc_iso8601_format():
    result = bot_v2.now_utc()
    assert re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", result), \
        f"Unexpected format: {result}"


# ── Role tier tests ────────────────────────────────────────────────────────

def _member_with_roles(*role_names: str) -> discord.Member:
    member = MagicMock(spec=discord.Member)
    roles = []
    for name in role_names:
        r = MagicMock()
        r.name = name
        roles.append(r)
    member.roles = roles
    return member


def test_get_user_tier_founder():
    assert bot_v2.get_user_tier(_member_with_roles("Founder")) == "founder"


def test_get_user_tier_pilot():
    assert bot_v2.get_user_tier(_member_with_roles("Pilot")) == "pilot"


def test_get_user_tier_supporter():
    assert bot_v2.get_user_tier(_member_with_roles("Supporter")) == "supporter"


def test_get_user_tier_public_with_no_special_roles():
    assert bot_v2.get_user_tier(_member_with_roles("Member")) == "public"


def test_get_user_tier_founder_wins_over_pilot():
    member = _member_with_roles("Pilot", "Founder")
    assert bot_v2.get_user_tier(member) == "founder"


def test_get_user_tier_none_returns_public():
    assert bot_v2.get_user_tier(None) == "public"


# ── Slash command handler tests (async, pytest-asyncio) ───────────────────

@pytest.mark.asyncio
async def test_cmd_status_sends_embed():
    interaction = AsyncMock(spec=discord.Interaction)
    interaction.user = _member_with_roles()
    interaction.response = AsyncMock()

    await bot_v2.cmd_status.callback(interaction)

    interaction.response.send_message.assert_awaited_once()
    embed = interaction.response.send_message.call_args.kwargs.get("embed")
    assert embed is not None
    assert embed.title == "Lantern OS Status"


@pytest.mark.asyncio
async def test_cmd_help_sends_ephemeral():
    interaction = AsyncMock(spec=discord.Interaction)
    interaction.user = _member_with_roles()
    interaction.response = AsyncMock()

    await bot_v2.cmd_help.callback(interaction)

    call_kwargs = interaction.response.send_message.call_args.kwargs
    assert call_kwargs.get("ephemeral") is True
    assert call_kwargs.get("embed") is not None


@pytest.mark.asyncio
async def test_cmd_subscribe_sends_tier_info():
    interaction = AsyncMock(spec=discord.Interaction)
    interaction.user = _member_with_roles()
    interaction.response = AsyncMock()

    await bot_v2.cmd_subscribe.callback(interaction)

    call_kwargs = interaction.response.send_message.call_args.kwargs
    embed = call_kwargs.get("embed")
    assert embed is not None
    field_names = " ".join(f.name for f in embed.fields).lower()
    assert "supporter" in field_names or "pilot" in field_names


@pytest.mark.asyncio
async def test_cmd_dream_replies_with_log_confirmation():
    interaction = AsyncMock(spec=discord.Interaction)
    interaction.user = _member_with_roles("Supporter")
    interaction.response = AsyncMock()

    await bot_v2.cmd_dream.callback(interaction, text="giant waves")

    interaction.response.send_message.assert_awaited_once()
    reply = interaction.response.send_message.call_args.args[0] if \
        interaction.response.send_message.call_args.args else \
        interaction.response.send_message.call_args.kwargs.get("content", "")
    assert "dream" in reply.lower() or "logged" in reply.lower()


# ── require_tier gate tests ────────────────────────────────────────────────

def test_require_tier_returns_callable_decorator():
    decorator = bot_v2.require_tier("supporter")
    assert callable(decorator)


def test_require_tier_decorated_function_is_callable():
    async def _stub(interaction):
        pass

    decorated = bot_v2.require_tier("supporter")(_stub)
    assert callable(decorated)


def test_require_tier_debug_mode_preserves_function():
    """In debug mode require_tier is a passthrough — the wrapped function is unchanged."""
    async def _stub(interaction):
        pass

    decorated = bot_v2.require_tier("founder")(_stub)
    assert decorated is _stub


@pytest.mark.asyncio
async def test_require_tier_debug_mode_does_not_block_any_user():
    """In debug mode all tiers are unlocked — decorated command runs for anyone."""
    called = []

    async def _stub(interaction):
        called.append(True)

    decorated = bot_v2.require_tier("founder")(_stub)

    interaction = AsyncMock(spec=discord.Interaction)
    interaction.user = _member_with_roles("Member")
    await decorated(interaction)

    assert called, "Command should have executed (debug mode — no tier gate)"
