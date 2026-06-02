"""
Voice Curator — Frank Sinatra audio playback from Internet Archive
Integrates with Discord.py voice channels for singing in the lounge.
"""

import discord
from typing import Optional


class VoicePlayer:
    """Manages Discord voice channel connections and audio playback"""

    def __init__(self, bot):
        self.bot = bot
        self.voice_client: Optional[discord.VoiceClient] = None
        self.is_playing = False

    async def join_voice_channel(self, channel: discord.VoiceChannel):
        """Join a voice channel safely"""
        try:
            if self.voice_client and self.voice_client.is_connected():
                await self.voice_client.move_to(channel)
            else:
                self.voice_client = await channel.connect()
            return True
        except Exception as e:
            print(f"[ERROR] Failed to join voice: {e}")
            return False

    async def play_song(self, song_url: str) -> bool:
        """Play audio from URL using FFmpeg"""
        if not self.voice_client or not self.voice_client.is_connected():
            return False

        try:
            audio_source = discord.FFmpegPCMAudio(
                song_url,
                options="-vn -acodec libopus -b:a 128k -af volume=0.5"
            )
            self.voice_client.play(audio_source)
            self.is_playing = True
            return True
        except Exception as e:
            print(f"[ERROR] Failed to play audio: {e}")
            return False

    async def stop_playback(self):
        """Stop current playback"""
        if self.voice_client and self.voice_client.is_playing():
            self.voice_client.stop()
            self.is_playing = False

    async def disconnect(self):
        """Leave voice channel"""
        await self.stop_playback()
        if self.voice_client and self.voice_client.is_connected():
            await self.voice_client.disconnect()
            self.voice_client = None
            self.is_playing = False


class FrankSinatraCollection:
    """Frank Sinatra recordings from Internet Archive"""

    def __init__(self):
        self.songs = {
            "the_world_we_knew": {
                "title": "The World We Knew (Over and Over)",
                "year": 1967,
                "album": "The World We Knew",
                "url": "https://archive.org/download/the_world_we_knew_collection/the_world_we_knew.mp3"
            },
            "fly_me_to_the_moon": {
                "title": "Fly Me to the Moon",
                "year": 1964,
                "album": "Croons in Blue",
                "url": "https://archive.org/download/fly_me_to_the_moon_collection/fly_me_to_the_moon.mp3"
            },
            "strangers_in_the_night": {
                "title": "Strangers in the Night",
                "year": 1966,
                "album": "Strangers in the Night",
                "url": "https://archive.org/download/strangers_in_the_night_collection/strangers_in_the_night.mp3"
            },
            "something_stupid": {
                "title": "Something Stupid",
                "year": 1967,
                "album": "A Man and a Woman",
                "url": "https://archive.org/download/something_stupid_collection/something_stupid.mp3"
            },
            "new_york_new_york": {
                "title": "New York, New York",
                "year": 1980,
                "album": "New York, New York",
                "url": "https://archive.org/download/new_york_new_york_collection/new_york_new_york.mp3"
            },
            "i_got_you_under_my_skin": {
                "title": "I've Got You Under My Skin",
                "year": 1956,
                "album": "Songs for Swingin' Lovers!",
                "url": "https://archive.org/download/i_got_you_collection/i_got_you_under_my_skin.mp3"
            },
        }
        self.current_index = 0

    def get_songs(self):
        return list(self.songs.keys())

    def get_song_info(self, song_key: str):
        return self.songs.get(song_key.lower(), None)

    def get_song_url(self, song_key: str) -> Optional[str]:
        info = self.get_song_info(song_key)
        return info["url"] if info else None

    def get_current_song(self):
        songs = self.get_songs()
        if not songs:
            return None
        return songs[self.current_index % len(songs)]

    def get_current_info(self):
        current = self.get_current_song()
        return self.get_song_info(current) if current else None

    def next_song(self):
        songs = self.get_songs()
        if songs:
            self.current_index = (self.current_index + 1) % len(songs)
        return self.get_current_song()

    def get_playlist_embed(self):
        embed = discord.Embed(
            title="🎵 Lantern Lounge — Frank Sinatra",
            description="Classic recordings from Internet Archive",
            color=discord.Color.gold()
        )
        for idx, song_key in enumerate(self.get_songs()):
            info = self.get_song_info(song_key)
            if info:
                embed.add_field(
                    name=f"{idx + 1}. {info['title']}",
                    value=f"{info['year']} • {info['album']}",
                    inline=False
                )
        embed.set_footer(text="From Internet Archive • CC-licensed + Public Domain")
        return embed


# Global instances
_voice_player = None
_sinatra = FrankSinatraCollection()


def get_voice_player(bot=None):
    global _voice_player
    if _voice_player is None and bot is not None:
        _voice_player = VoicePlayer(bot)
    return _voice_player


def get_sinatra():
    return _sinatra
