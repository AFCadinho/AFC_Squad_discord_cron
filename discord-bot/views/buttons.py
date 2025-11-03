import discord
# from database.database import Session
from cogs.tournament import Tournaments


class SignUpView(discord.ui.View):
    def __init__(self, bot, timeout: float | None = None):
        super().__init__(timeout=timeout)
        self.tournament = Tournaments(bot)

    @discord.ui.button(
        label="Sign Up",
        style=discord.ButtonStyle.green,
        emoji="📝",
        custom_id="tournament:sign_up"
    )
    async def sign_up(self, interaction: discord.Interaction, button: discord.ui.Button):        
        await self.tournament.sign_up_tournament(interaction)

    @discord.ui.button(
        label="Unregister",
        style=discord.ButtonStyle.red,
        emoji="⛔",
        custom_id="tournament:unregister"
    )
    async def unregister(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.tournament.unregister_tournament(interaction)
