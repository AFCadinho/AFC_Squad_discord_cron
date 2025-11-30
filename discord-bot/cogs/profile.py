import discord
from discord import app_commands, Embed
from discord.ext import commands
from views import ServerProfileView


class CrewProfile(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        self.bot.add_view(ServerProfileView(self.bot))

    @app_commands.command(
        name="profile_info",
        description="Display information about the MyProfile channel and tools."
    )
    @app_commands.default_permissions(administrator=True)
    async def profile_info(self, interaction: discord.Interaction):

        embed = Embed(
            title="MyProfile — Your AFC Squad Profile",
            description=(
                "This channel lets you view your personal AFC Squad profile and use tools that help us keep your information up to date.\n\n"
                "**Available actions:**\n"
                "• Open your Trainer Card\n"
                "• Update your Crew Wars wins\n"
                "• Check your current activity status\n"
                "• Set your timezone for better crew event alignment\n\n"
                "**Buttons in this channel:**\n"
                "• 🪪 **Trainer Card** – Shows your personal trainer card with your current info.\n"
                "• 🏆 **Update CWS Wins** – Lets you enter your **new total Crew Wars wins** so we can update your stats in our system.\n"
                "• 📊 **Check Activity Status** – Shows whether you are currently marked as active, safe, or inactive.\n\n"
                "**Useful commands:**\n"
                "• `/set_timezone` – Set your timezone so Crew Wars and event times can be shown correctly for you.\n"
                "• `/trainer_card` – View other players' trainer cards.\n"
            ),
            color=discord.Color.blue(),
        )

        view = ServerProfileView(self.bot)

        await interaction.response.send_message(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(CrewProfile(bot))
