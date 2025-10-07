import discord
import os

LOG_CHANNEL_ID = int(os.getenv("ERROR_LOGS_CH_ID", 0))

async def log_command_error(bot: discord.Client, interaction: discord.Interaction, error: Exception):
    """Send a simple error log embed to the log channel."""
    channel = bot.get_channel(LOG_CHANNEL_ID) or await bot.fetch_channel(LOG_CHANNEL_ID)
    if not channel:
        return

    embed = discord.Embed(title="❌ Command Error", color=discord.Color.red())
    embed.add_field(name="User", value=f"{interaction.user} (`{interaction.user.id}`)", inline=False)
    embed.add_field(name="Command", value=f"/{interaction.command.name}" if interaction.command else "N/A", inline=False)
    if isinstance(interaction.channel, discord.TextChannel):
        channel_value = interaction.channel.mention
    elif isinstance(interaction.channel, discord.DMChannel):
        channel_value = "Direct Message"
    elif isinstance(interaction.channel, discord.GroupChannel):
        channel_value = "Group Message"
    else:
        channel_value = "Unknown Channel"

    embed.add_field(name="Channel", value=channel_value, inline=False)
    embed.add_field(name="Error", value=f"```{error}```", inline=False)
    embed.timestamp = discord.utils.utcnow()

    if isinstance(channel, (discord.TextChannel, discord.DMChannel, discord.GroupChannel)):
        await channel.send(embed=embed)
