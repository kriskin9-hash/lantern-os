"""
Dream Journal RP Bot — Goal 1 Core
Minimal viable RP bot with IC/OOC handling and session lifecycle.
"""

import discord
from discord.ext import commands

from .memory_layer import memory_store, SessionMemory
from dream_journal.crystallization_engine import engine


class DreamJournalRPBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="/", intents=intents)

    async def on_ready(self):
        print(f"RP Bot online as {self.user}")

    @commands.command(name="dream")
    async def dream(self, ctx, action: str = "start", *, args: str = ""):
        """Main entry point for RP sessions."""
        user_id = ctx.author.id

        if action == "start":
            await self._start_session(ctx, user_id, args)
        elif action == "end":
            await self._end_session(ctx, user_id)
        elif action == "export":
            await self._export_session(ctx, user_id)
        else:
            await ctx.send("Unknown action. Use: start, end, export")

    @commands.command(name="crystallize")
    async def crystallize(self, ctx, *, dream_text: str):
        """Manually trigger crystallization on a dream."""
        user_id = ctx.author.id
        result = await engine.process_new_dream(user_id, dream_text)
        await ctx.send(f"Crystallization complete. New skill: {result.get('new_skill', {}).get('id', 'none')}")

    async def _start_session(self, ctx, user_id: int, args: str):
        session = memory_store.get_or_create(user_id, args or "default")
        await ctx.send(f"RP session started as **{session.character}**. In-character mode active.")

    async def _end_session(self, ctx, user_id: int):
        session = memory_store.end_session(user_id)
        if not session:
            await ctx.send("No active session.")
            return
        await ctx.send(f"Session ended. {len(session.messages)} messages recorded.")

    async def _export_session(self, ctx, user_id: int):
        session = memory_store.sessions.get(user_id)
        if not session:
            await ctx.send("No active session to export.")
            return
        jsonl = session.export_jsonl()
        await ctx.send(f"Export ready (JSONL). Messages: {len(session.messages)}")

    async def on_message(self, message):
        if message.author.bot:
            return

        user_id = message.author.id
        session = memory_store.sessions.get(user_id)

        if session:
            content = message.content

            if content.startswith("/ooc") or content.lower().startswith("(ooc"):
                session.add_message(content, mode="OOC")
                await message.channel.send("[OOC mode]")
            else:
                session.add_message(content, mode="IC")
                await message.channel.send(f"[{session.mode}] ...")

        await self.process_commands(message)


if __name__ == "__main__":
    # Entry point placeholder
    print("RP Bot module loaded. Run via launcher.")