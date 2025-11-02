import discord
import os
import logging

from discord.ext import commands
from discord import app_commands
from database.database import Session
from helpers import get_timezones, discord_id_to_member, CommandLogger, EmbedFactory
from zoneinfo import ZoneInfo
from datetime import datetime, timezone

MAX_CHOICES = 25
CWS_WINS_CHANNEL = int(os.getenv("CWS_WINS_CHANNEL_ID", 0))
log = logging.getLogger(__name__)


class WindsUpdateModal(discord.ui.Modal, title="Update Total Crew Wars Wins"):
    def __init__(self, cog: "Member", current_wins) -> None:
        super().__init__()
        self.cog = cog

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

        await self.cog.update_total_wins(interaction, int(new_wins))


class WinsUpdateView(discord.ui.View):
    def __init__(self, cog: "Member", timeout: float | None = None):
        super().__init__(timeout=timeout)
        self.cog = cog

    @discord.ui.button(
        label="Update Total Wins",
        style=discord.ButtonStyle.green,
        emoji="🏰",
        custom_id="cws_wins:updater"
    )
    async def button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):  
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

        modal = WindsUpdateModal(self.cog, crew_member.crew_wars_wins)
        await interaction.response.send_modal(modal)


class Member(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.command_logger = CommandLogger(bot)
        self.embed_factory = EmbedFactory(bot)

    async def cog_load(self):
        self.bot.add_view(WinsUpdateView(self))

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if not isinstance(message.channel, (discord.TextChannel)):
            return

        if message.channel.id != CWS_WINS_CHANNEL:
            return

        async for msg in message.channel.history(limit=20):
            if msg.author == self.bot.user:
                try:
                    await msg.delete()
                except Exception as e:
                    log.info(f"On Message Listener: {e}")

        embed = self.embed_factory.cw_update_reminder()

        await message.reply(
            embed=embed,
            view=WinsUpdateView(self),
            mention_author=False
        )

    async def update_total_wins(self, interaction: discord.Interaction, wins: int):
        discord_id = interaction.user.id
        discord_user = interaction.user
        if not isinstance(discord_user, discord.Member):
            return

        if not interaction.guild:
            return

        with Session.begin() as session:
            crew_member = discord_id_to_member(session, discord_id)

            if not crew_member:
                feedback = f"You are not registered in the database. Please contact staff"
                await interaction.response.send_message(feedback, ephemeral=True)
                await self.command_logger.discord_log(interaction.guild, "update_wins_cw", discord_user, error_msg=feedback)
                return

            new_wins_amount = wins
            current_wins = crew_member.crew_wars_wins
            if new_wins_amount < current_wins:
                feedback = f"The amount of wins has to be greater than the current amount of wins.\nCurrent wins: {current_wins}"
                await interaction.response.send_message(f"The amount of wins has to be greater than the current amount of wins.\nCurrent wins: {current_wins}", ephemeral=True)
                await self.command_logger.discord_log(interaction.guild, "update_wins_cw", discord_user, error_msg=feedback)
                return

            crew_member.crew_wars_wins = new_wins_amount
            await interaction.response.send_message(f"{crew_member.username}'s Crew Wars Victories successfully updated\nOld Value: {current_wins}\nNew Value: {new_wins_amount}", ephemeral=True)
            await self.command_logger.discord_log(interaction.guild, "update_wins_cw", discord_user)

    async def autocomplete_timezone_name(self, interaction: discord.Interaction, current: str):
        user = interaction.user
        if not user:
            return []

        with Session() as session:

            crew_member = discord_id_to_member(session, user.id)
            if not crew_member:
                return []

            country_name = crew_member.country
            if not country_name:
                return []

            timezone_names = get_timezones(country_name) or []

        search_text = (current or "").lower()
        if search_text:
            timezone_names = [
                tz for tz in timezone_names if search_text in tz.lower()]

        timezone_names = timezone_names[:MAX_CHOICES]

        return [
            app_commands.Choice(name=tz, value=tz)
            for tz in timezone_names
        ]

    @app_commands.command(name="set_timezone", description="Set the correct timezone for your account for timezone related commands")
    async def set_timezone(self, interaction: discord.Interaction, timezone_name: str):
        try:
            ZoneInfo(timezone_name)
        except Exception:
            await interaction.response.send_message(
                "❌ Invalid timezone. Please pick from the suggestions.",
                ephemeral=True
            )
            return

        with Session.begin() as session:
            crew_member = discord_id_to_member(session, interaction.user.id)
            if not crew_member:
                await interaction.response.send_message(f"You are not registered in our database. Please contact management", ephemeral=True)
                return

            country_name = crew_member.country
            if not country_name:
                await interaction.response.send_message(f"No Country set for this user. Please contact management", ephemeral=True)
                return

            timezone_names = get_timezones(country_name)
            if not timezone_names:
                await interaction.response.send_message(f"No Timezone list available for country: {country_name}", ephemeral=True)
                return
            tz_name = None
            for tz in timezone_names:
                if timezone_name.lower() == tz.lower():
                    tz_name = tz

            if not tz_name:
                await interaction.response.send_message(f"The inputted timezone name does not exist for country: {country_name}", ephemeral=True)
                return

            crew_member.timezone_name = tz_name
            await interaction.response.send_message(f"Timezone successfully updated to: {tz_name}", ephemeral=True)

    @set_timezone.autocomplete("timezone_name")
    async def autocomplete_set_timezone(self, interaction: discord.Interaction, current: str):
        return await self.autocomplete_timezone_name(interaction, current)

    @app_commands.command(name="update_wins_cw", description="Update the amount of Crew Wars Victories you have")
    async def update_wins_cw(self, interaction: discord.Interaction, wins: int):
        await self.update_total_wins(interaction, wins)

    @app_commands.command(name="trainer_card", description="View a crew member's Trainer Card")
    async def trainer_card(self, interaction: discord.Interaction, user: discord.Member, hidden: bool = False):
        with Session() as session:
            row = discord_id_to_member(session, user.id)
            if not row:
                await interaction.response.send_message(f"No record found for {user.mention}.", ephemeral=True)
                return

            total_wins = len(row.won_tournaments)

            embed = discord.Embed(
                title=f"🎴 {row.username}'s Trainer Card",
                color=discord.Color.blurple()
            )
            embed.set_author(name=user.display_name, icon_url=getattr(
                user.display_avatar, "url", None))
            embed.set_thumbnail(url=getattr(user.display_avatar, "url", None))

            embed.add_field(name="IGN", value=row.username or "—", inline=True)
            embed.add_field(name="Active", value=(
                "✅ Yes" if row.is_active else "❌ No"), inline=True)
            embed.add_field(name="PvP Experience", value=(
                row.pvp_experience or "—").title(), inline=True)
            embed.add_field(
                name="Join Date",
                value=row.created_at.strftime(
                    "%d-%m-%Y") if row.created_at else "—",
                inline=True
            )
            embed.add_field(name="🏆 CW Victories",
                            value=f"{row.crew_wars_wins:,}", inline=True)
            embed.add_field(name="🏅 Tournament Wins",
                            value=str(total_wins), inline=True)

            if total_wins > 0:
                embed.add_field(
                    name="More",
                    value=f"Use `/show_won_tournaments` to see all wins.",
                    inline=False
                )

        if hidden:
            await interaction.response.send_message(embed=embed, ephemeral=False)
            return

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="show_won_tournaments", description="List all the crew tournaments that a crew member has won")
    async def show_won_tournaments(self, interaction: discord.Interaction, trainer: discord.Member):
        with Session() as session:
            discord_user = interaction.user
            crew_member = discord_id_to_member(session, discord_user.id)
            crew_trainer = discord_id_to_member(session, trainer.id)

            if not crew_member:
                await interaction.response.send_message("❌ You have to be a crew member to use this command.", ephemeral=True)
                return

            if not crew_trainer:
                await interaction.response.send_message("❌ No records found for this trainer.", ephemeral=True)
                return

            total_wins = len(crew_trainer.won_tournaments)
            if total_wins == 0:
                await interaction.response.send_message(f"{trainer.mention} has no tournament wins yet.", ephemeral=False)
                return

            embed = discord.Embed(
                title=f"🏅 {crew_trainer.username}'s Tournament Wins",
                color=discord.Color.gold()
            )
            embed.set_author(name=trainer.display_name, icon_url=getattr(
                trainer.display_avatar, "url", None))

            # Build the tournament list
            lines = []
            for t in crew_trainer.won_tournaments:
                name = getattr(t, "name", "Unnamed Tournament")
                url = getattr(t, "url", None)
                if url:
                    lines.append(f"• [{name}]({url})")
                else:
                    lines.append(f"• {name}")

            embed.description = "\n".join(lines[:25])

            embed.set_footer(text=f"Total Wins: {total_wins}")

        await interaction.response.send_message(embed=embed, ephemeral=False)

    @app_commands.command(name="edit_join_date", description="Edit the join date of a crew member")
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(
        member="Crew member whose join date you want to edit",
        date_str="New join date (format: YYYY-MM-DD)",
    )
    async def edit_join_date(self, interaction: discord.Interaction, member: discord.Member, date_str: str):
        await interaction.response.defer(ephemeral=True, thinking=True)

        try:
            new_dt = datetime.strptime(
                date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            await interaction.followup.send(
                "❌ Invalid date format. Please use **YYYY-MM-DD** (e.g. `2025-10-31`).",
                ephemeral=True
            )
            return

        with Session.begin() as session:
            crew_member = discord_id_to_member(session, member.id)
            if not crew_member:
                await interaction.followup.send(f"Crew member is not registered in our database.")
                return

            old_dt = crew_member.created_at
            crew_member.created_at = new_dt

            embed = discord.Embed(
                title="✅ Join Date Updated",
                color=discord.Color.green(),
                description=f"**{member.display_name}**’s join date has been updated."
            )
            if old_dt:
                embed.add_field(
                    name="Previous", value=f"<t:{int(old_dt.timestamp())}:F>", inline=False)
            embed.add_field(
                name="New", value=f"<t:{int(new_dt.timestamp())}:F> (UTC)", inline=False)

            await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Member(bot))
