import os
import discord
from discord.ext import commands
import asyncio

SIGNUPS_CH = int(os.getenv("SIGNUPS_CH_ID", 0))
REPORTS_CH = int(os.getenv("REPORTS_CH_ID", 0))

CHANNELS_TO_AUTOCLEAN = {ch for ch in [SIGNUPS_CH, REPORTS_CH] if ch}


class AutoClean(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Ignore DMs, non-target channels, or system messages
        if not message.guild or message.channel.id not in CHANNELS_TO_AUTOCLEAN:
            return

        # Don't delete the bot’s own messages
        if message.author.id == self.bot.user.id:
            return

        # (Optional) Skip other bots
        if message.author.bot:
            return

        try:
            await message.delete()
            # Send a brief reminder that disappears
            note = await message.channel.send(
                f"{message.author.mention}, this channel is **command-only**.\n"
                "Please use the slash commands shown in the pinned embed."
            )
            await asyncio.sleep(4)
            await note.delete()
        except discord.Forbidden:
            # Bot doesn’t have Manage Messages
            pass
        except discord.HTTPException:
            # Already deleted / rate limit issues
            pass


async def setup(bot: commands.Bot):
    await bot.add_cog(AutoClean(bot))
