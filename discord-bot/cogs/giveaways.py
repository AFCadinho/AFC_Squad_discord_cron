import discord
import os

from discord.ext import commands
from discord import app_commands
from database.models import GiveAway
from database.database import Session
from helpers import EmbedFactory
from helpers import parse_duration_string, get_timeout_seconds
from sqlalchemy import select  


GIVEAWAY_CH = os.getenv("GIVEAWAY_CH_ID", 0)


class GiveawayView(discord.ui.View):
    def __init__(self, session_factory, timeout: float | None = None):
        super().__init__(timeout=timeout)
        self.session_factory = session_factory

    @discord.ui.button(
        label="Enter",
        style=discord.ButtonStyle.green,
        emoji="🎉",
        custom_id="giveaway:enter"
    )
    async def button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(f"🎉 | You have entered the giveaway!", ephemeral=True)


class Giveaways(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.embed = EmbedFactory(bot)

    async def cog_load(self):
        self.bot.add_view(GiveawayView(Session))

    @app_commands.command(name="gcreate", description="Create a giveaway")
    @app_commands.default_permissions(administrator=True)
    async def gcreate(self, interaction: discord.Interaction, channel: discord.TextChannel, duration: str, prize: str, winners: int = 1):
        try:
            end_dt = parse_duration_string(duration)
        except ValueError as e:
            await interaction.response.send_message(f"{e}", ephemeral=True)
            return

        timeout_seconds = get_timeout_seconds(end_dt)     
        embed = self.embed.giveaway_embed(
            prize=prize.title(),
            winners=winners,
            end_time=end_dt,
            participants=0
        )
        
        message = await channel.send(embed=embed, view=GiveawayView(Session, timeout=timeout_seconds))

        with Session.begin() as session:
            
            new_giveaway = GiveAway(
                end_date=end_dt,
                name=prize.lower(),
                message_id=message.id
            )

            session.add(new_giveaway)
            session.commit()

        await interaction.response.send_message(
            f"✅ Giveaway created in {channel.mention} (message ID: `{message.id}`)",
            ephemeral=True
        )


    @app_commands.command(name="gdelete", description="Delete a giveaway")
    @app_commands.default_permissions(administrator=True)
    async def gdelete(self, interaction: discord.Interaction, message_id: str):
        if not message_id.isdigit():
            await interaction.response.send_message(f"Input has to be a digit. e.g. 69")
            return
        
        with Session.begin() as session:
            stmt = (
                select(GiveAway)
                .where(GiveAway.message_id == int(message_id))
            )
            give_away = session.scalars(stmt).first()
            if not give_away:
                await interaction.response.send_message(f"No giveaway found with this message id: {message_id}")
                return

            
            
            session.delete(give_away)
            session.commit()
            
            await interaction.response.send_message(f"Giveaway successfully deleted.\nMessage_ID : {message_id}")

async def setup(bot: commands.Bot):
    await bot.add_cog(Giveaways(bot))
