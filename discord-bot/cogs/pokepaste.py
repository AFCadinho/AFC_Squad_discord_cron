import discord
from discord import app_commands
from discord.ext import commands
import tempfile
from generate_team_image import generate_team_image

class PokepasteCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="pp", description="Generate an image from a Pokepaste link")
    @app_commands.describe(link="The Pokepaste link")
    async def pp(self, interaction: discord.Interaction, link: str):
        await interaction.response.defer()  # in case it takes time

        try:
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                generate_team_image(link, filename=tmp.name)
                tmp.seek(0)
                await interaction.followup.send(file=discord.File(tmp.name, filename="team.png"))
        except Exception as e:
            await interaction.followup.send(f"❌ Failed to generate image: {e}")

async def setup(bot):
    await bot.add_cog(PokepasteCog(bot))
