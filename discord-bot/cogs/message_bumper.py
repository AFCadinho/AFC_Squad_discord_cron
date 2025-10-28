import discord
from discord.ext import commands
import asyncio
import os

SCHEDULING_CH = int(os.getenv("SCHEDULING_CH_ID", 0))
SCHEDULING_EMBED_TITLE = "📅 Scheduling Your Match"

class SchedulingEmbedWatcher(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # import your real embed builder here if it exists
    def _scheduling_reminder_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title=SCHEDULING_EMBED_TITLE,
            description=(
                "⚠️ **This channel is command-only.**\n"
                "Only use the slash command below after you and your opponent agreed on a time.\n\n"
                "• One of the players runs:\n"
                "`/schedule_match opponent:@Opponent round:<#> year:YYYY month:MM day:DD hour:HH minute:MM`\n\n"
                "📌 Example:\n"
                "`/schedule_match opponent:@Player2 round:1 year:2025 month:10 day:5 hour:19 minute:00`\n\n"
                "✅ Matches must be scheduled **before Wednesday (PBO in-game time)**\n"
                "✅ You may play earlier than the scheduled time, but not later."
            ),
            color=discord.Color.blue(),
        )
        embed.set_footer(text="Only one schedule per match is needed.")
        return embed

    async def _delete_previous_scheduling_embed(self, channel: discord.abc.Messageable):
        """Remove the most recent scheduling embed posted by the bot."""
        async for msg in channel.history(limit=50):
            if msg.author == self.bot.user and msg.embeds:
                e = msg.embeds[0]
                if (e.title or "").strip() == SCHEDULING_EMBED_TITLE:
                    try:
                        await msg.delete()
                    except discord.HTTPException:
                        pass
                    break

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Only act inside the scheduling channel
        if not message.guild or message.channel.id != SCHEDULING_CH:
            return
        if not self.bot.user:
            return
        
        # Only react to the bot’s own messages
        if message.author.id != self.bot.user.id:
            return
        # Ignore when it’s already the scheduling embed
        if message.embeds and (message.embeds[0].title or "").strip() == SCHEDULING_EMBED_TITLE:
            return

        # Wait a moment so the bot finishes posting its new message
        await asyncio.sleep(0.5)

        # Delete the previous scheduling embed (if any)
        await self._delete_previous_scheduling_embed(message.channel)

        # Repost the scheduling embed at the bottom
        try:
            await message.channel.send(embed=self._scheduling_reminder_embed())
        except discord.HTTPException:
            pass


async def setup(bot: commands.Bot):
    await bot.add_cog(SchedulingEmbedWatcher(bot))
