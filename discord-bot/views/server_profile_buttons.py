import discord
from cogs.members import Member
from database.database import Session
from helpers import discord_id_to_member


class WindsUpdateModal(discord.ui.Modal, title="Update Total Crew Wars Wins"):
    def __init__(self, member_cog: Member, current_wins) -> None:
        super().__init__()
        self.member_cog = member_cog

        self.wins = discord.ui.TextInput(
            label=f"Total Wins",
            placeholder="Enter your total Crew Wars victories (e.g. 69)",
            default=str(current_wins) if current_wins is not None else None,
            required=True,
            max_length=6
        )
        self.add_item(self.wins)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        new_wins = self.wins.value.strip()
        if not new_wins.isdigit():
            await interaction.response.send_message(
                "❌ Please enter a valid number.",
                ephemeral=True
            )
            return

        await self.member_cog.update_total_wins(interaction, int(new_wins))


class ServerProfileView(discord.ui.View):
    def __init__(self, bot, timeout: float | None = None):
        super().__init__(timeout=timeout)
        self.member = Member(bot)

    @discord.ui.button(
        label="Trainer Card",
        style=discord.ButtonStyle.primary,
        emoji="🪪",
        custom_id="trainer:card"
    )
    async def next_cws(self, interaction: discord.Interaction, button: discord.ui.Button):        
        if not isinstance(interaction.user, discord.Member):
            return
        
        embed = await self.member.show_trainer_card(interaction, interaction.user)
        if not embed:
            return
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(
        label="Update CWS Wins",
        style=discord.ButtonStyle.success,
        emoji="🏆",
        custom_id="profile:update_cws_wins"
    )

    async def update_cws_wins(self, interaction: discord.Interaction, button: discord.ui.Button):  
        discord_member = interaction.user
        if not isinstance(discord_member, discord.Member):
            return
        
        with Session() as session:
            crew_member = discord_id_to_member(session, discord_member.id)
            if not crew_member:
                await interaction.response.send_message(
                    "❌ You are not registered in the database. Please contact staff.",
                    ephemeral=True
                )
                return

        modal = WindsUpdateModal(self.member, crew_member.crew_wars_wins)
        await interaction.response.send_modal(modal)

    @discord.ui.button(
        label="Activity Status",
        style=discord.ButtonStyle.secondary,
        emoji="📊",
        custom_id="profile:activity_status"
    )
    async def activity_status(self, interaction: discord.Interaction, button: discord.ui.Button):

        if not isinstance(interaction.user, discord.Member):
            return
        
        embed = await self.member.show_activity_status(interaction.user)
        if not embed:
            return

        await interaction.response.send_message(embed=embed, ephemeral=True)