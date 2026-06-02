"""
Robust Music Queue for Lantern OS Discord Bot

Uses yt-dlp for reliable audio extraction + discord.py voice streaming.
Features: queue, skip, pause, resume, clear, auto-disconnect on empty queue.
"""

import asyncio
import discord
from typing import Optional, List, Dict
from pathlib import Path

try:
    import yt_dlp
    YTDLP_AVAILABLE = True
except ImportError:
    YTDLP_AVAILABLE = False
    yt_dlp = None

YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'quiet': True,
    'no_warnings': True,
    'extractaudio': True,
    'audioformat': 'mp3',
    'noplaylist': True,
    'nocheckcertificate': True,
    'geo_bypass': True,
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn -loglevel warning'
}


class GuildMusicQueue:
    """Per-guild music queue with auto-advance."""

    def __init__(self, guild_id: int, voice_client: discord.VoiceClient):
        self.guild_id = guild_id
        self.voice_client = voice_client
        self.queue: List[Dict] = []
        self.current: Optional[Dict] = None
        self._is_playing = False
        self._loop = False

    async def add(self, query: str) -> Optional[Dict]:
        """Add a song to the queue via yt-dlp extraction."""
        if not YTDLP_AVAILABLE:
            raise RuntimeError("yt-dlp not installed. Run: pip install yt-dlp")

        # If not a URL, search YouTube
        if not query.startswith("http"):
            query = f"ytsearch1:{query}"

        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(query, download=False)
            if "entries" in info:
                info = info["entries"][0]
            title = info.get("title", "Unknown")
            audio_url = info["url"]

        song = {"url": audio_url, "title": title, "original_query": query}
        self.queue.append(song)
        return song

    async def play_next(self):
        """Play next song or disconnect if queue empty."""
        if not self.queue:
            self._is_playing = False
            self.current = None
            if self.voice_client and self.voice_client.is_connected():
                await self.voice_client.disconnect(force=True)
            return

        song = self.queue.pop(0)
        self.current = song
        self._is_playing = True

        try:
            source = discord.FFmpegPCMAudio(song["url"], **FFMPEG_OPTIONS)
            self.voice_client.play(
                source,
                after=lambda e: asyncio.run_coroutine_threadsafe(
                    self._after_play(e), asyncio.get_event_loop()
                )
            )
        except Exception as e:
            print(f"[MUSIC] Playback error: {e}")
            await self.play_next()

    async def _after_play(self, error):
        if error:
            print(f"[MUSIC] After-play error: {error}")
        if self._loop and self.current:
            self.queue.insert(0, self.current)
        await self.play_next()

    def skip(self) -> bool:
        if self.voice_client and self.voice_client.is_playing():
            self.voice_client.stop()
            return True
        return False

    def pause(self) -> bool:
        if self.voice_client and self.voice_client.is_playing():
            self.voice_client.pause()
            return True
        return False

    def resume(self) -> bool:
        if self.voice_client and self.voice_client.is_paused():
            self.voice_client.resume()
            return True
        return False

    def clear(self):
        self.queue.clear()
        if self.voice_client and self.voice_client.is_playing():
            self.voice_client.stop()
        self.current = None
        self._is_playing = False

    def get_queue(self) -> List[str]:
        return [s["title"] for s in self.queue]

    def now_playing(self) -> Optional[str]:
        return self.current["title"] if self.current else None

    def set_loop(self, enabled: bool):
        self._loop = enabled


class MusicQueueManager:
    """Global manager for per-guild music queues."""

    def __init__(self):
        self._queues: Dict[int, GuildMusicQueue] = {}

    def get_queue(self, guild_id: int, voice_client: discord.VoiceClient) -> GuildMusicQueue:
        if guild_id not in self._queues:
            self._queues[guild_id] = GuildMusicQueue(guild_id, voice_client)
        return self._queues[guild_id]

    def remove_queue(self, guild_id: int):
        self._queues.pop(guild_id, None)


# Global manager instance
music_manager = MusicQueueManager()
