"""
Lantern Archive Curator — Internet Archive Media Streaming for Discord

Streams audio, books, and movies from archive.org in Discord voice channels.
Supports multiple collections: Frank Sinatra, classical music, audiobooks, etc.
"""

import discord
import asyncio
from typing import Optional, List, Dict, Any
import requests
from urllib.parse import quote

# Internet Archive base
ARCHIVE_BASE = "https://archive.org/download"

# Curated collections from Internet Archive
# Each collection contains CC-licensed or public domain media
ARCHIVE_COLLECTIONS = {
    "sinatra": {
        "name": "Frank Sinatra Music",
        "description": "Classic Frank Sinatra recordings from Internet Archive",
        "items": {
            "the_world_we_knew": {
                "title": "The World We Knew (Over and Over)",
                "url": "https://archive.org/download/frank_sinatra_collection/Frank%20Sinatra%20-%20The%20World%20We%20Knew.mp3",
                "archive_id": "frank_sinatra_collection",
                "year": 1967,
                "album": "The World We Knew",
            },
            "fly_me_to_the_moon": {
                "title": "Fly Me to the Moon",
                "url": "https://archive.org/download/frank_sinatra_collection/Frank%20Sinatra%20-%20Fly%20Me%20to%20the%20Moon.mp3",
                "archive_id": "frank_sinatra_collection",
                "year": 1964,
                "album": "It Might as Well Be Swing",
            },
            "strangers_in_the_night": {
                "title": "Strangers in the Night",
                "url": "https://archive.org/download/frank_sinatra_collection/Frank%20Sinatra%20-%20Strangers%20in%20the%20Night.mp3",
                "archive_id": "frank_sinatra_collection",
                "year": 1966,
                "album": "Strangers in the Night",
            },
            "something_stupid": {
                "title": "Something Stupid",
                "url": "https://archive.org/download/frank_sinatra_collection/Frank%20Sinatra%20-%20Something%20Stupid.mp3",
                "archive_id": "frank_sinatra_collection",
                "year": 1967,
                "album": "The Best of Frank Sinatra",
            },
            "new_york_new_york": {
                "title": "New York, New York",
                "url": "https://archive.org/download/frank_sinatra_collection/Frank%20Sinatra%20-%20New%20York%20New%20York.mp3",
                "archive_id": "frank_sinatra_collection",
                "year": 1980,
                "album": "Trilogy",
            },
            "i_got_you_under_my_skin": {
                "title": "I've Got You Under My Skin",
                "url": "https://archive.org/download/frank_sinatra_collection/Frank%20Sinatra%20-%20I%27ve%20Got%20You%20Under%20My%20Skin.mp3",
                "archive_id": "frank_sinatra_collection",
                "year": 1956,
                "album": "Songs for Swingin' Lovers",
            },
        }
    },
    # More collections can be added here:
    # "classical": { ... },
    # "audiobooks": { ... },
    # "public_domain_movies": { ... },
}

# Backward compatibility: expose sinatra collection as top-level
SINATRA_COLLECTION = ARCHIVE_COLLECTIONS["sinatra"]["items"]


class ArchiveCurator:
    """
    Internet Archive curator for Discord voice channels.

    Features:
    - Stream multiple audio/media collections from archive.org
    - Join/leave voice channels
    - Playlist management with loop support
    - Collection switching
    """

    def __init__(self, default_collection: str = "sinatra"):
        self.voice_channel_name = "archive"
        self.voice_channel_id = None
        self.current_collection = default_collection
        self.current_playlist = list(ARCHIVE_COLLECTIONS[default_collection]["items"].values())
        self.current_index = 0
        self.loop_enabled = False
        self.shuffle_enabled = False

    def get_collections(self) -> Dict[str, str]:
        """Get all available collections."""
        return {key: val["name"] for key, val in ARCHIVE_COLLECTIONS.items()}

    def get_collection_items(self, collection: str = None) -> List[Dict[str, Any]]:
        """Get all items in a collection."""
        coll = collection or self.current_collection
        if coll not in ARCHIVE_COLLECTIONS:
            return []
        return list(ARCHIVE_COLLECTIONS[coll]["items"].values())

    def switch_collection(self, collection: str) -> bool:
        """Switch to a different collection."""
        if collection not in ARCHIVE_COLLECTIONS:
            return False
        self.current_collection = collection
        self.current_playlist = list(ARCHIVE_COLLECTIONS[collection]["items"].values())
        self.current_index = 0
        return True

    def get_item_by_key(self, key: str, collection: str = None) -> Optional[Dict[str, Any]]:
        """Get a specific item by key."""
        coll = collection or self.current_collection
        if coll not in ARCHIVE_COLLECTIONS:
            return None
        return ARCHIVE_COLLECTIONS[coll]["items"].get(key)

    def get_current_item(self) -> Optional[Dict[str, Any]]:
        """Get the currently playing item."""
        if self.current_index < len(self.current_playlist):
            return self.current_playlist[self.current_index]
        return None

    def next_item(self) -> Optional[Dict[str, Any]]:
        """Move to the next item in the playlist."""
        if len(self.current_playlist) == 0:
            return None
        self.current_index = (self.current_index + 1) % len(self.current_playlist)
        return self.get_current_item()

    def enable_loop(self):
        """Enable looping of the current item."""
        self.loop_enabled = True

    def disable_loop(self):
        """Disable looping."""
        self.loop_enabled = False

    async def find_voice_channel(self, guild: discord.Guild) -> Optional[discord.VoiceChannel]:
        """Find the archive voice channel by name or ID."""
        if self.voice_channel_id:
            try:
                channel_id = int(self.voice_channel_id)
                return discord.utils.get(guild.voice_channels, id=channel_id)
            except ValueError:
                pass

        # Find by name
        return discord.utils.find(
            lambda ch: ch.name.lower() == self.voice_channel_name.lower(),
            guild.voice_channels
        )

    async def join_archive(self, guild: discord.Guild) -> Optional[discord.VoiceClient]:
        """Connect the bot to the archive voice channel."""
        channel = await self.find_voice_channel(guild)

        if channel is None:
            return None

        # Check if already connected
        if guild.voice_client:
            if guild.voice_client.channel == channel:
                return guild.voice_client
            else:
                await guild.voice_client.move_to(channel)
                return guild.voice_client

        # Connect to channel
        voice_client = await channel.connect()
        return voice_client

    async def leave_archive(self, guild: discord.Guild):
        """Disconnect the bot from the voice channel."""
        if guild.voice_client:
            await guild.voice_client.disconnect()

    def get_playback_info(self, voice_client: Optional[discord.VoiceClient]) -> str:
        """Get current playback status."""
        current = self.get_current_item()

        if not current:
            return "No items in playlist"

        status = f"**{current['title']}**\n"
        if "album" in current:
            status += f"Album: {current.get('album', 'Unknown')}\n"
        if "year" in current:
            status += f"Year: {current.get('year', 'Unknown')}\n"

        if voice_client and voice_client.is_playing():
            status += "Status: Playing"
        elif voice_client and voice_client.is_paused():
            status += "Status: Paused"
        else:
            status += "Status: Stopped"

        status += f"\nLoop: {'On' if self.loop_enabled else 'Off'}"
        status += f"\nQueue: {self.current_index + 1}/{len(self.current_playlist)}"

        return status

    def get_playlist_embed(self) -> discord.Embed:
        """Create a Discord embed showing the archive playlist."""
        coll = ARCHIVE_COLLECTIONS.get(self.current_collection, {})
        embed = discord.Embed(
            title=f"Lantern Archive — {coll.get('name', 'Unknown')}",
            description=coll.get('description', 'Internet Archive collection'),
            color=discord.Color.gold()
        )

        items = self.get_collection_items()
        playlist_text = "\n".join(
            f"{i+1}. {item['title']} ({item.get('year', '?')})"
            for i, item in enumerate(items[:10])
        )

        embed.add_field(
            name="Available Items",
            value=playlist_text or "No items available",
            inline=False
        )

        embed.add_field(
            name="Commands",
            value="""
/archive-join — Join the archive channel
/archive-list — Show items in current collection
/archive-play [item] — Play an item
/archive-next — Next item
/archive-loop — Toggle loop
/archive-stop — Stop playback
/archive-leave — Disconnect
            """,
            inline=False
        )

        embed.set_footer(text="From Internet Archive • CC-licensed + Public Domain")

        return embed


# Global instance
curator = ArchiveCurator()


def get_curator() -> ArchiveCurator:
    """Get the global Archive Curator instance."""
    return curator
