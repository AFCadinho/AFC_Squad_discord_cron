import discord
from discord.ext import commands
from discord import app_commands
# from database.models import User
from database.database import Session
from helpers import get_timezones, discord_id_to_member
from zoneinfo import ZoneInfo

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
                await interaction.response.send_message(f"You are not registered in our database. Please contact management" , ephemeral=True)
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


async def setup(bot: commands.Bot):
    await bot.add_cog(Member(bot))
