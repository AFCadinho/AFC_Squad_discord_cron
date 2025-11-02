import os
import discord
from .embed_factory import EmbedFactory

COMMAND_LOG_CH = int(os.getenv("COMMAND_LOG_CH_ID", 0))

class CommandLogger:
    def __init__(self, bot) -> None:
        self.bot = bot
        self.embed_factory = EmbedFactory(bot)

    async def discord_log(self, guild: discord.Guild, command_name: str, discord_user: discord.Member, error_msg: str | None=None):
        if not guild or not COMMAND_LOG_CH:
            return
        
        embed = self.embed_factory.discord_log(discord_user, command_name, error_msg=error_msg)
        
        command_log_ch = guild.get_channel(COMMAND_LOG_CH)
        if not isinstance(command_log_ch, discord.TextChannel):
            return
        
        await command_log_ch.send(embed=embed)
