import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import os

load_dotenv()


class ApplicationLogger(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    APP_TRANSCRIPT_ID = int(os.getenv("APP_TRANSCRIPT_ID", "0"))

    @app_commands.command(name="log_application", description="Log a crew application transcript")
    @app_commands.describe(
        user="Select the applicant",
        link="Transcript link from Tickety"
    )
    async def log_application(self, interaction: discord.Interaction, user: discord.User, link: str):
        embed = discord.Embed(
            title="📥 New Crew Application Logged",
            color=discord.Color.blue()
        )
        embed.add_field(name="👤 User", value=f"{user.mention} (`{user}`)", inline=False)
        embed.add_field(name="📝 Transcript", value=f"[View Transcript]({link})", inline=False)
        embed.add_field(name="🕐 Date", value=discord.utils.format_dt(discord.utils.utcnow(), style='F'), inline=False)
        embed.set_footer(text="AFC Squad | Pokémon Blaze Online", icon_url=self.bot.user.display_avatar.url)

        log_channel = self.bot.get_channel(self.APP_TRANSCRIPT_ID)
        if log_channel:
            await log_channel.send(
                content=f"🆕 Application logged for {user.mention}",
                embed=embed
            )
            await interaction.response.send_message("✅ Application logged successfully.", ephemeral=True)

        else:
            await interaction.response.send_message("❌ Log channel not found.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ApplicationLogger(bot))
