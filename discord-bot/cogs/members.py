import discord
from discord.ext import commands
from discord import app_commands
from database.database import Session
from helpers import get_timezones, discord_id_to_member
from zoneinfo import ZoneInfo
from helpers import discord_id_to_member

MAX_CHOICES = 25


class Member(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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
    async def update_wins_cw(self, interaction: discord.Interaction, wins: str):
        discord_id = interaction.user.id

        with Session.begin() as session:
            crew_member = discord_id_to_member(session, discord_id)

            if not crew_member:
                await interaction.response.send_message(f"You are not registered in the database. Please contact staff", ephemeral=True)
                return

            if not wins.isdigit():
                await interaction.response.send_message(f"The amount of wins has to be a digit. e.g. 69", ephemeral=True)
                return

            new_wins_amount = int(wins)
            current_wins = crew_member.crew_wars_wins
            if new_wins_amount < current_wins:
                await interaction.response.send_message(f"The amount of wins has to be greater than the current amount of wins.\nCurrent wins: {current_wins}", ephemeral=True)
                return

            crew_member.crew_wars_wins = new_wins_amount
            await interaction.response.send_message(f"{crew_member.username}'s Crew Wars Victories successfully updated\nOld Value: {current_wins}\nNew Value: {new_wins_amount}", ephemeral=True)

    @app_commands.command(name="trainer_card", description="View a crew member's Trainer Card")
    async def trainer_card(self, interaction: discord.Interaction, user: discord.Member, hidden: bool=False):
        with Session() as session:
            row = discord_id_to_member(session, user.id)
            if not row:
                await interaction.response.send_message(f"No record found for {user.mention}.", ephemeral=True)
                return

            # Safely compute wins count while session is open
            total_wins = len(row.won_tournaments)

            embed = discord.Embed(
                title=f"🎴 {row.username}'s Trainer Card",
                color=discord.Color.blurple()
            )
            embed.set_author(name=user.display_name, icon_url=getattr(user.display_avatar, "url", None))
            embed.set_thumbnail(url=getattr(user.display_avatar, "url", None))

            embed.add_field(name="IGN", value=row.username or "—", inline=True)
            embed.add_field(name="Active", value=("✅ Yes" if row.is_active else "❌ No"), inline=True)
            embed.add_field(name="PvP Experience", value=(row.pvp_experience or "—").title(), inline=True)
            embed.add_field(
                name="Join Date",
                value=row.created_at.strftime("%d-%m-%Y") if row.created_at else "—",
                inline=True
            )
            embed.add_field(name="🏆 CW Victories", value=f"{row.crew_wars_wins:,}", inline=True)
            embed.add_field(name="🏅 Tournament Wins", value=str(total_wins), inline=True)

            if total_wins > 0:
                embed.add_field(
                    name="More",
                    value=f"Use `/show_won_tournaments` to see all wins.",
                    inline=False
                )

        if not hidden:
            await interaction.response.send_message(embed=embed, ephemeral=False)
        
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
            embed.set_author(name=trainer.display_name, icon_url=getattr(trainer.display_avatar, "url", None))

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



async def setup(bot: commands.Bot):
    await bot.add_cog(Member(bot))
