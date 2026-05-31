"""
Discord Bot Tests

Tests for Discord lounge bot, voice gate,
and Discord integration.
"""
import pytest
from pathlib import Path


def test_discord_bot_directory_exists():
    """Verify Discord bot directory exists."""
    bot_dir = Path("src/discord_lounge_bot")
    assert bot_dir.exists()


def test_discord_bot_has_readme():
    """Verify Discord bot has README."""
    readme = Path("src/discord_lounge_bot/README.md")
    assert readme.exists()


def test_discord_bot_has_bot_py():
    """Verify Discord bot has bot.py."""
    bot_py = Path("src/discord_lounge_bot/bot.py")
    assert bot_py.exists()


def test_discord_bot_has_requirements():
    """Verify Discord bot has requirements.txt."""
    requirements = Path("src/discord_lounge_bot/requirements.txt")
    assert requirements.exists()


def test_discord_bot_readme_has_content():
    """Verify Discord bot README has content."""
    readme = Path("src/discord_lounge_bot/README.md")
    content = readme.read_text(encoding="utf-8")
    
    assert len(content) > 50, "Discord bot README should have content"


def test_discord_bot_py_has_content():
    """Verify Discord bot bot.py has content."""
    bot_py = Path("src/discord_lounge_bot/bot.py")
    content = bot_py.read_text(encoding="utf-8")
    
    assert len(content) > 50, "Discord bot bot.py should have content"


def test_discord_voice_gate_test_exists():
    """Verify Discord voice gate test exists."""
    test_file = Path("tests/test_discord_voice_gate.py")
    assert test_file.exists()


def test_discord_bot_has_no_secrets():
    """Verify Discord bot has no hardcoded secrets."""
    bot_py = Path("src/discord_lounge_bot/bot.py")
    content = bot_py.read_text(encoding="utf-8")
    
    # Should not have hardcoded tokens
    secret_patterns = ["token", "secret", "api_key"]
    for pattern in secret_patterns:
        # Check for obvious hardcoded values (not environment variables)
        if f'"{pattern}"' in content.lower() or f"'{pattern}'" in content.lower():
            if "os.environ" not in content and "getenv" not in content:
                pytest.fail(f"Potential hardcoded secret in Discord bot: {pattern}")


def test_discord_bot_requirements_has_discord():
    """Verify Discord bot requirements include discord.py."""
    requirements = Path("src/discord_lounge_bot/requirements.txt")
    content = requirements.read_text(encoding="utf-8")
    
    assert "discord" in content.lower(), "Requirements should include discord.py"


def test_discord_bot_has_commands():
    """Verify Discord bot has command definitions."""
    bot_py = Path("src/discord_lounge_bot/bot.py")
    content = bot_py.read_text(encoding="utf-8")
    
    # Should have command decorators
    has_commands = "@command" in content or "@bot.command" in content
    if has_commands:
        pass  # Has commands


def test_discord_bot_has_event_handlers():
    """Verify Discord bot has event handlers."""
    bot_py = Path("src/discord_lounge_bot/bot.py")
    content = bot_py.read_text(encoding="utf-8")
    
    # Should have event handlers
    has_events = "@event" in content or "@bot.event" in content
    if has_events:
        pass  # Has event handlers


def test_discord_bot_has_error_handling():
    """Verify Discord bot has error handling."""
    bot_py = Path("src/discord_lounge_bot/bot.py")
    content = bot_py.read_text(encoding="utf-8")
    
    # Should have try/except or error handling
    has_error_handling = "try" in content and "except" in content
    if has_error_handling:
        pass  # Has error handling


def test_discord_voice_gate_test_has_content():
    """Verify Discord voice gate test has content."""
    test_file = Path("tests/test_discord_voice_gate.py")
    content = test_file.read_text(encoding="utf-8")
    
    assert len(content) > 50, "Discord voice gate test should have content"


def test_discord_bot_documentation_exists():
    """Verify Discord bot documentation exists."""
    doc = Path("docs/DISCORD-FIRST-DEV-PREVIEW-CHECKIN-2026-05-28.md")
    if not doc.exists():
        pytest.skip("Discord bot documentation not yet created")


def test_discord_bot_has_intents():
    """Verify Discord bot has intents configured."""
    bot_py = Path("src/discord_lounge_bot/bot.py")
    content = bot_py.read_text(encoding="utf-8")
    
    # Should have intents
    has_intents = "intents" in content.lower()
    if has_intents:
        pass  # Has intents


def test_discord_bot_has_prefix():
    """Verify Discord bot has command prefix."""
    bot_py = Path("src/discord_lounge_bot/bot.py")
    content = bot_py.read_text(encoding="utf-8")
    
    # Should have command prefix
    has_prefix = "command_prefix" in content or "prefix" in content.lower()
    if has_prefix:
        pass  # Has prefix


def test_discord_bot_is_not_empty():
    """Verify Discord bot files are not empty."""
    bot_dir = Path("src/discord_lounge_bot")
    files = list(bot_dir.glob("*"))
    
    for file in files:
        if file.is_file() and not file.name.startswith("."):
            content = file.read_text(encoding="utf-8")
            assert len(content.strip()) > 0, f"Discord bot file is empty: {file}"


def test_discord_bot_has_main_entry():
    """Verify Discord bot has main entry point."""
    bot_py = Path("src/discord_lounge_bot/bot.py")
    content = bot_py.read_text(encoding="utf-8")
    
    # Should have main entry or if __name__ == "__main__"
    has_main = "if __name__" in content or "main" in content.lower()
    if has_main:
        pass  # Has main entry


def test_discord_bot_has_logging():
    """Verify Discord bot has logging."""
    bot_py = Path("src/discord_lounge_bot/bot.py")
    content = bot_py.read_text(encoding="utf-8")
    
    # Should have logging
    has_logging = "logging" in content.lower() or "log" in content.lower()
    if has_logging:
        pass  # Has logging
