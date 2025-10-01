import challonge.api
import discord
import os
import challonge

from discord import app_commands
from discord.ext import commands
from sqlalchemy import select
from database.database import Session
from database.models import Tournament

# Global Variable
USERNAME = os.getenv("CH_USERNAME")
API_KEY = os.getenv("CH_API_KEY")


def auth_tournament():
    if not USERNAME or not API_KEY:
        raise RuntimeError(
            "Missing Challonge credentials (CH_USERNAME / CH_API_KEY).")
    challonge.set_credentials(USERNAME, API_KEY)


def fetch_current_tournament():
    with Session.begin() as session:
        stmt = select(Tournament).where(Tournament.current_tournament == True)
        current_tournament = session.scalars(stmt).first()
        return current_tournament.slug if current_tournament else None


def slugify(string):
    return string.replace(" ", "_").lower()


class Tournaments(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        auth_tournament()
        self.current_tournament = fetch_current_tournament()

    @staticmethod
    def check_if_exists(session, slug):
        stmt = select(Tournament).where(Tournament.slug == slug)
        return session.scalars(stmt).first()

    @staticmethod
    def get_challonge_id(slug):
        tournament = challonge.tournaments.show(slug)
        tournament_id = tournament["id"]  # type: ignore
        return tournament_id if tournament_id else None

    async def autocomplete_tournament_name(self, interaction: discord.Interaction, current: str):
        session = Session()
        with session:
            stmt = select(Tournament).order_by(Tournament.ongoing)
            tournaments = session.scalars(stmt).all()

            return [
                app_commands.Choice(name=t.name, value=t.slug)
                for t in tournaments
            ]

    @app_commands.command(name="set_current_tournament", description="Matches all the tournament commands to a specific tournament")
    @app_commands.default_permissions(administrator=True)
    async def set_current_tournament(self, interaction: discord.Interaction, name: str):
        with Session.begin() as session:
            slug = slugify(name)
            tournament = self.check_if_exists(session, slug)
            if not tournament:
                await interaction.response.send_message(f"Tournament with name '{name}' does not exist.", ephemeral=True)

            stmt = select(Tournament).where(
                Tournament.current_tournament == True)
            tournaments = session.scalars(stmt).all()
            if tournament:
                for t in tournaments:
                    t.current_tournament = False

            tournament.current_tournament = True
            self.current_tournament = slug

        await interaction.response.send_message(f"The current tournament is set to: {self.current_tournament}", ephemeral=True)

    @app_commands.command(name="get_current_tournament", description="Shows the current tournament that be bot is managing")
    @app_commands.default_permissions(administrator=True)
    async def get_current_tournament(self, interaction: discord.Interaction):
        current_tournament_slug = self.current_tournament
        if not current_tournament_slug:
            await interaction.response.send_message(f"I am currently not managing any tournament")
            return

        session = Session()
        with session:
            tournament = self.check_if_exists(session, current_tournament_slug)
            if not tournament:
                await interaction.response.send_message(f"The tournament im managing doesn't exist: '{current_tournament_slug}'")
                return

            tournament_summary = str(tournament)
            await interaction.response.send_message(tournament_summary)

    @app_commands.command(name="create_tournament", description="Create tournament of Challonge")
    @app_commands.default_permissions(administrator=True)
    async def create_tournament(self, interaction: discord.Interaction, name: str):
        slug = slugify(name)
        try:
            challonge.tournaments.create(
                name=name,
                url=slug,
                tournament_type="single elimination"
            )

        except challonge.api.ChallongeException as e:
            await interaction.response.send_message(f"Could not create tournament because:\n{e}", ephemeral=True)
            return

        with Session.begin() as session:
            existing_tournament = self.check_if_exists(session, slug)
            if existing_tournament:
                await interaction.response.send_message(f"Could not create tournament, because:\nTournament already exists", ephemeral=True)
                return

            tournament_url = f"https://challonge.com/{slug}"

            new_tournament = Tournament(
                challonge_id=self.get_challonge_id(slug),
                name=name,
                slug=slug,
                url=tournament_url
            )

            session.add(new_tournament)
            tournament_url = new_tournament.url

        await interaction.response.send_message(f"Tournament: '{slug}' successfully created\nSee bracket at {tournament_url}", ephemeral=True)

    @app_commands.command(name="delete_tournament", description="Delete an existing tournament")
    @app_commands.default_permissions(administrator=True)
    async def delete_tournament(self, interaction: discord.Interaction, name: str):
        slug = slugify(name)
        with Session.begin() as session:
            tournament = self.check_if_exists(session, slug)
            if not tournament:
                await interaction.response.send_message(f"Tournament '{slug}' does not exist.", ephemeral=True)
                return

            challonge.tournaments.destroy(slug)
            deleted_tournament_slug = tournament.slug
            session.delete(tournament)
            if slug == self.current_tournament:
                self.current_tournament = None

        await interaction.response.send_message(f"Tournament '{deleted_tournament_slug}' deleted", ephemeral=True)

    @delete_tournament.autocomplete("name")
    @set_current_tournament.autocomplete("name")
    async def autocomplete_tournament(self, interaction: discord.Interaction, current: str):
        return await self.autocomplete_tournament_name(interaction, current)


async def setup(bot: commands.Bot):
    await bot.add_cog(Tournaments(bot))
