param(
    [string]$GuildId = $env:LANTERN_DISCORD_GUILD_ID,
    [string]$Token = $env:DISCORD_BOT_TOKEN,
    [string]$Manifest = "manifests/DISCORD-COMMUNITY-CONVERGENCE.md"
)

$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
$manifestPath = Join-Path $root $Manifest

if (-not (Test-Path -LiteralPath $manifestPath)) {
    throw "Manifest not found: $manifestPath"
}

if (-not $Token) {
    throw "DISCORD_BOT_TOKEN is not set. Dry run cannot inspect a server."
}

if (-not $GuildId) {
    Write-Output (@{
        ok = $false
        mode = "dry-run"
        applied = $false
        reason = "No guild/server ID provided. Set LANTERN_DISCORD_GUILD_ID or pass -GuildId."
        manifest = $Manifest
    } | ConvertTo-Json -Depth 6)
    exit 0
}

$python = @"
import asyncio
import json
import os
import re
from pathlib import Path

token = os.environ.get("DISCORD_BOT_TOKEN")
guild_id = int(os.environ.get("LANTERN_DISCORD_GUILD_ID_FOR_DRY_RUN", "0"))
manifest = Path(r"$manifestPath")

desired = []
for line in manifest.read_text(encoding="utf-8").splitlines():
    if line.startswith("|") and "`" in line:
        desired.extend(re.findall(r"`([^`]+)`", line))

desired = [name for name in desired if name.startswith("#") or name == "Lounge"]

async def main():
    try:
        import discord
    except Exception as exc:
        print(json.dumps({
            "ok": False,
            "mode": "dry-run",
            "applied": False,
            "reason": "discord.py is not installed in this Python environment",
            "error": str(exc),
            "desiredChannels": desired,
        }, indent=2))
        return

    intents = discord.Intents.default()
    intents.guilds = True
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        guild = client.get_guild(guild_id)
        if guild is None:
            await client.close()
            print(json.dumps({
                "ok": False,
                "mode": "dry-run",
                "applied": False,
                "reason": "Bot cannot see the requested guild/server ID",
                "guildId": guild_id,
                "desiredChannels": desired,
            }, indent=2))
            return

        existing_text = {"#" + c.name for c in guild.text_channels}
        existing_voice = {c.name for c in guild.voice_channels}
        existing = existing_text | existing_voice
        missing = [c for c in desired if c not in existing]

        print(json.dumps({
            "ok": True,
            "mode": "dry-run",
            "applied": False,
            "guildName": guild.name,
            "guildId": guild.id,
            "existingMatched": sorted([c for c in desired if c in existing]),
            "wouldCreateOrReview": missing,
            "note": "No Discord changes were applied.",
        }, indent=2))
        await client.close()

    await client.start(token)

asyncio.run(main())
"@

$env:LANTERN_DISCORD_GUILD_ID_FOR_DRY_RUN = $GuildId
$temp = Join-Path $env:TEMP ("lantern-discord-community-dry-run-{0}-{1}.py" -f $PID, ([guid]::NewGuid().ToString("N")))
$python | Set-Content -LiteralPath $temp -Encoding UTF8
try {
    python $temp
}
finally {
    Remove-Item -LiteralPath $temp -Force -ErrorAction SilentlyContinue
}
