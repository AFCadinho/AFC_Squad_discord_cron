import discord
from cogs.crewwars import CrewWars
from cogs.game_tools import GameTools


class ServerToolsView(discord.ui.View):
    def __init__(self, bot, timeout: float | None = None):
        super().__init__(timeout=timeout)
        self.crew_wars = CrewWars(bot)
        self.game_tools = GameTools(bot)

    @discord.ui.button(
        label="Next CWS",
        style=discord.ButtonStyle.success,
        emoji="📝",
        custom_id="cws:next"
    )
    async def next_cws(self, interaction: discord.Interaction, button: discord.ui.Button):        
        embed = await self.crew_wars.next_cws()
        if not embed:
            return
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(
        label="CWS Schedule",
        style=discord.ButtonStyle.primary,
        custom_id="cws:schedule"
    )
    async def cws_schedule(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = await self.crew_wars.show_cws_schedule()
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(
        label="Tide",
        style=discord.ButtonStyle.secondary,
        emoji="🌊",
        custom_id="tide:show"
    )
    async def tide(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.game_tools.show_tide(interaction)
