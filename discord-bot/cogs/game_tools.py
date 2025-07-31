import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta, timezone
import os

class GameTools(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="tide", description="Check if it's currently Low Tide or High Tide at Shoal Cave.")
    async def tide(self, interaction: discord.Interaction):
        now = datetime.now(timezone.utc)
        hour = now.hour
        minute = now.minute
        total_minutes = hour * 60 + minute

        block = total_minutes // 180
        is_low_tide = block % 2 == 0
        tide_status = "🌊 **Low Tide**" if is_low_tide else "🌊 **High Tide**"

        next_change_minutes = ((block + 1) * 180) % (24 * 60)
        next_change = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(minutes=next_change_minutes)

        # Create the embed
        embed = discord.Embed(
            title="Tide Status – Shoal Cave",
            description=f"It is currently {tide_status}.",
            color=discord.Color.teal()
        )
        embed.add_field(
            name="Next Tide Change",
            value=f"<t:{int(next_change.timestamp())}:R> (at <t:{int(next_change.timestamp())}:t> UTC)",
            inline=False
        )
        embed.set_footer(text="Tide changes every 3 hours (UTC)")
        embed.set_image(url="attachment://shoal_tide_chart.png")

        # Path to your image in the root images folder
        root_dir = os.path.dirname(os.path.abspath(__file__))  # current file dir
        file_path = os.path.join(root_dir, "..", "images", "shoal_tide_chart.png")
        file_path = os.path.normpath(file_path)  # normalize to clean up path

        file = discord.File(file_path, filename="shoal_tide_chart.png")

        await interaction.response.send_message(embed=embed, file=file, ephemeral=True)

async def setup(bot):
    await bot.add_cog(GameTools(bot))
