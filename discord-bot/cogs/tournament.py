import challonge.api
import discord
import os
import challonge
import requests
import sqlalchemy as sa
import validators

from datetime import datetime, timezone
from discord import app_commands
from discord.ext import commands
from sqlalchemy import select
from database.database import Session
from database.models import Tournament, User, TournamentParticipants, TournamentMatches
from helpers import country_to_timezone, discord_id_to_member
from zoneinfo import ZoneInfo

# Global Variable
USERNAME = os.getenv("CH_USERNAME")
API_KEY = os.getenv("CH_API_KEY")
GUILD_ID = os.getenv("GUILD_ID", 0)

SIGNUPS_CH = int(os.getenv("SIGNUPS_CH_ID", 0))
REPORTS_CH = int(os.getenv("REPORTS_CH_ID", 0))
VIDEO_CHANNEL = int(os.getenv("VIDEO_CH_ID", 0))
ANNOUNCEMENT_CH = int(os.getenv("ANNOUNCEMENTS_CH_ID", 0))
LOGS_CH = int(os.getenv("LOGS_CH_ID", 0))
SCHEDULING_CH = int(os.getenv("SCHEDULING_CH_ID", 0))


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


def slugify(string) -> str | None:
    if not string:
        return None
    return string.replace(" ", "_").lower()


class Tournaments(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        auth_tournament()
        self.current_tournament = fetch_current_tournament()

    # Static Methods ---------------------------------
    @staticmethod
    def __get_participant_from_id(session, participant_id):
        stmt = select(TournamentParticipants).where(
            TournamentParticipants.id == participant_id)
        return session.scalars(stmt).first()

    @staticmethod
    def build_simple_embed(title: str, description: str, color: discord.Color):
        embed = discord.Embed(
            title=title,
            description=description,
            color=color)
        embed.timestamp = discord.utils.utcnow()
        return embed

    @staticmethod
    def __check_if_tournament(session, slug):
        stmt = select(Tournament).where(Tournament.slug == slug)
        return session.scalars(stmt).first()

    @staticmethod
    def __get_challonge_id(slug):
        tournament = challonge.tournaments.show(slug)
        tournament_id = tournament["id"]  # type: ignore
        return tournament_id if tournament_id else None

    @staticmethod
    def __user_id_to_member(session, user_id):
        stmt = select(User).where(User.id == user_id)
        return session.scalars(stmt).first()

    @staticmethod
    def __check_if_participant(session, tournament_id, user_id):
        stmt = select(TournamentParticipants).where(
            TournamentParticipants.user_id == user_id,
            TournamentParticipants.tournament_id == tournament_id)
        return session.scalars(stmt).first()

    @staticmethod
    def __get_match_row_for_players(session, tournament_id, p1_id, p2_id):
        stmt = select(TournamentMatches).where(
            TournamentMatches.tournament_id == tournament_id,
            sa.or_(
                sa.and_(
                    TournamentMatches.participant1_id == p1_id,
                    TournamentMatches.participant2_id == p2_id),

                sa.and_(
                    TournamentMatches.participant1_id == p2_id,
                    TournamentMatches.participant2_id == p1_id),
            ),
            TournamentMatches.completed == False
        ).limit(1)
        return session.scalars(stmt).first()

    @staticmethod
    def __get_match_row_by_chid(session, tournament_id: int, match_ch_id: int):
        stmt = select(TournamentMatches).where(
            TournamentMatches.tournament_id == tournament_id,
            TournamentMatches.challonge_id == match_ch_id,
        )
        return session.scalars(stmt).first()

    @staticmethod
    def __find_next_match_player(slug, player_challonge_id):
        next_match = None
        try:
            player_matches = challonge.matches.index(
                slug, participant_id=player_challonge_id)
        except:
            return next_match

        for match in player_matches:
            if match["state"] != "complete":  # type: ignore
                return match

        return None

    @staticmethod
    def __find_current_match_player(slug, player_challonge_id):
        next_match = None
        try:
            player_matches = challonge.matches.index(
                slug, participant_id=player_challonge_id)
        except:
            return next_match

        for match in player_matches:
            if match["state"] == "open":  # type: ignore
                return match

        return None

    @staticmethod
    def __p_challonge_id_to_participant(session, tournament_id, p_challonge_id):
        stmt = select(TournamentParticipants).where(
            TournamentParticipants.tournament_id == tournament_id,
            TournamentParticipants.challonge_id == p_challonge_id
        )
        return session.scalars(stmt).first()

    @staticmethod
    def get_participant_on_rank(slug, rank):
        try:
            participants_ch = challonge.participants.index(slug)
        except challonge.api.ChallongeException:
            return None

        for participant in participants_ch:
            participant_rank = participant["final_rank"]  # type: ignore
            if participant_rank == rank:
                return participant["id"]  # type: ignore

        return None

    async def _log_to_logs(self, *, title: str, description: str = "", fields: dict[str, str] | None = None):
        """Send a small embed to the logs channel. Safe no-op if channel missing/inaccessible."""
        logs_channel = LOGS_CH
        if not logs_channel:
            return

        ch = self.bot.get_channel(logs_channel)
        if ch is None:
            try:
                ch = await self.bot.fetch_channel(logs_channel)
            except Exception:
                return  # can't reach logs channel; bail quietly

        print("CREATING EMBED FOR LOGS CHANNEL")
        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color.blurple()
        )
        embed.timestamp = discord.utils.utcnow()
        if fields:
            for name, value in fields.items():
                embed.add_field(name=name, value=value or "—", inline=False)

        try:
            await ch.send(embed=embed)
        except Exception:
            pass

    async def __autocomplete_all_tournament_names(self, interaction: discord.Interaction, current: str):
        session = Session()
        with session:
            stmt = select(Tournament).order_by(Tournament.ongoing)
            tournaments = session.scalars(stmt).all()

            return [
                app_commands.Choice(name=t.name, value=t.slug)
                for t in tournaments
            ]

    async def __autocomplete_unfinished_names(self, interaction: discord.Interaction, current: str):
        session = Session()
        with session:
            stmt = select(Tournament).where(
                Tournament.winner_id == None
            )
            tournaments = session.scalars(stmt).all()

            return [
                app_commands.Choice(name=t.name, value=t.slug)
                for t in tournaments
            ]

    async def __autocomplete_new_tournaments(self, interaction: discord.Interaction, current: str):
        session = Session()
        with session:
            stmt = select(Tournament).where(Tournament.ongoing == False)
            tournaments = session.scalars(stmt).all()

            return [
                app_commands.Choice(name=t.name, value=t.slug)
                for t in tournaments
            ]

    # TOURNAMENT MANAGEMENT -----------------------
    async def __prep_next_match_winner(self, session, slug, winner_challonge_id):
        next_match = self.__find_next_match_player(slug, winner_challonge_id)
        if not next_match:
            return False

        tournament = self.__check_if_tournament(session, slug)
        if not tournament:
            return False

        chall_player1_id = next_match["player1_id"]  # type: ignore
        chall_player2_id = next_match["player2_id"]  # type: ignore

        participant1 = self.__p_challonge_id_to_participant(
            session, tournament.id, chall_player1_id)
        participant2 = self.__p_challonge_id_to_participant(
            session, tournament.id, chall_player2_id)

        next_match_challonge_id = next_match["id"]  # type: ignore
        stmt = select(TournamentMatches).where(
            TournamentMatches.challonge_id == next_match_challonge_id)
        next_match_row = session.scalars(stmt).first()
        next_match_row.participant1_id = participant1.id if participant1 else None
        next_match_row.participant2_id = participant2.id if participant2 else None

        return True

    async def insert_matches_in_db(self, session, tournament_matches, tournament):
        for match in tournament_matches:
            challonge_p1_id = match["player1_id"]
            challonge_p2_id = match["player2_id"]

            stmt1 = select(TournamentParticipants).where(
                TournamentParticipants.challonge_id == challonge_p1_id
            )

            stmt2 = select(TournamentParticipants).where(
                TournamentParticipants.challonge_id == challonge_p2_id
            )

            player1 = session.scalars(stmt1).first()
            player2 = session.scalars(stmt2).first()

            tournament_match = TournamentMatches(
                tournament_id=tournament.id,
                participant1_id=player1.id if player1 else None,
                participant2_id=player2.id if player2 else None,
                challonge_id=match["id"],
                round=match["round"]
            )
            session.add(tournament_match)

    @app_commands.command(name="set_current_tournament", description="Matches all the tournament commands to a specific tournament")
    @app_commands.default_permissions(administrator=True)
    async def set_current_tournament(self, interaction: discord.Interaction, name: str):
        with Session.begin() as session:
            slug = slugify(name)
            tournament = self.__check_if_tournament(session, slug)
            if not tournament:
                await interaction.response.send_message(
                    embed=self.build_simple_embed(
                        "❌ Error", f"Tournament with name **{name}** does not exist.", discord.Color.red()),
                    ephemeral=True
                )
                return

            stmt = select(Tournament).where(
                Tournament.current_tournament == True)
            tournaments = session.scalars(stmt).all()
            if tournament:
                for t in tournaments:
                    t.current_tournament = False

            tournament.current_tournament = True
            self.current_tournament = slug

        await interaction.response.send_message(
            embed=self.build_simple_embed(
                "✅ Current Tournament Set", f"Now managing: **{self.current_tournament}**", discord.Color.green()),
            ephemeral=True
        )

    @app_commands.command(name="get_current_tournament", description="Shows the current tournament that be bot is managing")
    @app_commands.default_permissions(administrator=True)
    async def get_current_tournament(self, interaction: discord.Interaction):
        current_tournament_slug = self.current_tournament
        if not current_tournament_slug:
            await interaction.response.send_message(
                embed=self.build_simple_embed(
                    "ℹ️ Info", "I am currently not managing any tournament.", discord.Color.blurple()),
                ephemeral=True
            )
            return

        session = Session()
        with session:
            tournament = self.__check_if_tournament(
                session, current_tournament_slug)
            if not tournament:
                await interaction.response.send_message(
                    embed=self.build_simple_embed(
                        "❌ Error", f"The tournament I’m managing doesn’t exist: **{current_tournament_slug}**", discord.Color.red()),
                    ephemeral=True
                )
                return

            await interaction.response.send_message(
                embed=self.build_simple_embed(
                    "🏆 Current Tournament", str(tournament), discord.Color.green()),
                ephemeral=True
            )

    @app_commands.command(name="create_tournament", description="Create tournament of Challonge")
    @app_commands.default_permissions(administrator=True)
    async def create_tournament(self, interaction: discord.Interaction, name: str):
        slug = slugify(name)

        with Session.begin() as session:
            existing_tournament = self.__check_if_tournament(session, slug)
            if existing_tournament:
                await interaction.response.send_message(
                    embed=self.build_simple_embed(
                        "❌ Cannot Create", "Tournament already exists.", discord.Color.red()),
                    ephemeral=True
                )
                return

            try:
                challonge.tournaments.create(
                    name=name,
                    url=slug,
                    tournament_type="single elimination",
                    hold_third_place_match=True
                )

            except challonge.api.ChallongeException as e:
                await interaction.response.send_message(
                    embed=self.build_simple_embed(
                        "❌ Cannot Create", f"{e}", discord.Color.red()),
                    ephemeral=True
                )
                return

            tournament_url = f"https://challonge.com/{slug}"

            new_tournament = Tournament(
                challonge_id=self.__get_challonge_id(slug),
                name=name,
                slug=slug,
                url=tournament_url
            )

            session.add(new_tournament)
            tournament_url = new_tournament.url

        await interaction.response.send_message(
            embed=self.build_simple_embed(
                "✅ Tournament Created", f"**{slug}**\nSee bracket: {tournament_url}", discord.Color.green()),
            ephemeral=True
        )

    @app_commands.command(name="delete_tournament", description="Delete an existing tournament")
    @app_commands.default_permissions(administrator=True)
    async def delete_tournament(self, interaction: discord.Interaction, name: str):
        slug = slugify(name)
        with Session.begin() as session:
            tournament = self.__check_if_tournament(session, slug)
            if not tournament:
                await interaction.response.send_message(
                    embed=self.build_simple_embed(
                        "❌ Error", f"Tournament **{slug}** does not exist.", discord.Color.red()),
                    ephemeral=True
                )
                return

            remote_delete_error_msg = None
            try:
                challonge.tournaments.destroy(slug)
            except challonge.api.ChallongeException as e:
                remote_delete_error_msg = str(e)
            except requests.HTTPError as e:
                if e.response is not None and e.response.status_code == 404:
                    pass  # already gone on Challonge, that's fine
                else:
                    remote_delete_error_msg = str(e)

            deleted_tournament_slug = tournament.slug
            session.delete(tournament)
            if slug == self.current_tournament:
                self.current_tournament = None

        msg = f"Tournament **{deleted_tournament_slug}** deleted."
        if remote_delete_error_msg:
            msg = msg + "\n\n**Remote delete failed**:\n" + remote_delete_error_msg

        await interaction.response.send_message(
            embed=self.build_simple_embed(
                "🗑️ Delete Tournament", msg, discord.Color.orange()),
            ephemeral=True
        )

    @app_commands.command(name="start_tournament", description="Start a specific tournament")
    @app_commands.default_permissions(administrator=True)
    async def start_tournament(self, interaction: discord.Interaction, name: str):
        slug = slugify(name)
        with Session.begin() as session:
            tournament = self.__check_if_tournament(session, slug)
            if not tournament:
                await interaction.response.send_message(
                    embed=self.build_simple_embed(
                        "❌ Error", f"Tournament **{name}** does not exist.", discord.Color.red()),
                    ephemeral=True
                )
                return

            if tournament.ongoing:
                await interaction.response.send_message(
                    embed=self.build_simple_embed(
                        "ℹ️ Info", f"Tournament **{name}** is already ongoing.", discord.Color.blurple()),
                    ephemeral=True
                )
                return

            try:
                challonge.participants.randomize(slug)
                challonge.tournaments.start(slug)
            except challonge.api.ChallongeException as e:
                await interaction.response.send_message(
                    embed=self.build_simple_embed(
                        "❌ Could Not Start", f"{e}", discord.Color.red()),
                    ephemeral=True
                )
                return
            error_message = None

            try:
                tournament_matches = challonge.matches.index(slug)
                await self.insert_matches_in_db(session, tournament_matches, tournament)
            except challonge.api.ChallongeException as e:
                error_message = str(e)

            tournament.ongoing = True
            msg = f"Tournament **{name}** has now started."

            if error_message:
                msg += "\n\n**Warning**:\n" + error_message

        await interaction.response.send_message(
            embed=self.build_simple_embed(
                "🚀 Tournament Started", msg, discord.Color.green()),
            ephemeral=True)

    @app_commands.command(name="end_tournament", description="End a specific ongoing tournament")
    @app_commands.default_permissions(administrator=True)
    async def end_tournament(self, interaction: discord.Interaction):
        slug = slugify(self.current_tournament)

        try:
            challonge.tournaments.finalize(slug)
        except challonge.api.ChallongeException as e:
            await interaction.response.send_message(
                embed=self.build_simple_embed(
                    "❌ Could Not End", f"{e}", discord.Color.red()),
                ephemeral=True
            )
            return

        with Session.begin() as session:

            tournament = self.__check_if_tournament(session, slug)
            if not tournament:
                await interaction.response.send_message(
                    embed=self.build_simple_embed(
                        "ℹ️ Info", "There is currently no tournament running.", discord.Color.blurple()),
                    ephemeral=True
                )
                return

            challonge_winner_id = self.get_participant_on_rank(slug, 1)
            if not challonge_winner_id:
                await interaction.response.send_message(
                    embed=self.build_simple_embed(
                        "ℹ️ Info", "No winner available. Tournament hasn’t been finalized.", discord.Color.blurple()),
                    ephemeral=True
                )
                return

            participant_winner = self.__p_challonge_id_to_participant(
                session, tournament.id, challonge_winner_id)
            if not participant_winner:
                await interaction.response.send_message(
                    embed=self.build_simple_embed(
                        "❌ Error", "Winner is not registered as a participant.", discord.Color.red()),
                    ephemeral=True
                )
                return

            crew_member = self.__user_id_to_member(
                session, participant_winner.id)
            if not crew_member:
                await interaction.response.send_message(
                    embed=self.build_simple_embed(
                        "❌ Error", "Winner does not exist in our database.", discord.Color.red()),
                    ephemeral=True
                )
                return

            tournament.winner_id = crew_member.id
            tournament.ongoing = False
            self.current_tournament = None
            await interaction.response.send_message(
                embed=self.build_simple_embed(
                    "🏁 Tournament Ended",
                    f"**{tournament.name}**\nWinner: **{crew_member.username}**\nBracket: {tournament.url}",
                    discord.Color.green()
                ),
                ephemeral=True
            )

    # Auto complete handlers -----------------------------------------------

    @set_current_tournament.autocomplete("name")
    async def auto_complete_ongoing_tournament(self, interaction: discord.Interaction, current: str):
        return await self.__autocomplete_unfinished_names(interaction, current)

    @start_tournament.autocomplete("name")
    async def auto_complete_new_tournament(self, interaction: discord.Interaction, current: str):
        return await self.__autocomplete_new_tournaments(interaction, current)

    @delete_tournament.autocomplete("name")
    async def autocomplete_tournament(self, interaction: discord.Interaction, current: str):
        return await self.__autocomplete_all_tournament_names(interaction, current)

    # PARTICIPANTS MANAGEMENT -----------------------------------

    async def __delete_player_from_bracket(self, player_challonge_id, slug):
        try:
            challonge.participants.destroy(slug, player_challonge_id)
            return "Player successfully remove from challonge bracket"
        except challonge.api.ChallongeException as e:
            return f"Unable to remove player from challonge bracket. Reason: \n{e}"

    async def __remove_player_from_tournament(self, member, slug):
        with Session.begin() as session:
            tournament = self.__check_if_tournament(session, slug)
            if not tournament:
                return "The ongoing tournament does not exist in the database."

            crew_member = discord_id_to_member(session, member.id)
            if not crew_member:
                return f"{member.name} does not exist in our database"

            stmt = select(TournamentParticipants).where(
                TournamentParticipants.user_id == crew_member.id,
                TournamentParticipants.tournament_id == tournament.id
            )
            participant = session.scalars(stmt).first()
            if not participant:
                return f"{member.name} is not participating in this tournament: {tournament.name}"

            player_challonge_id = participant.challonge_id
            msg = await self.__delete_player_from_bracket(player_challonge_id, slug)

            session.delete(participant)
            return msg

    async def __add_player_to_tournament(self, member, slug):
        with Session.begin() as session:
            tournament = self.__check_if_tournament(session, slug)
            if not tournament:
                return None, "The ongoing tournament does not exist in the database."

            crew_member = discord_id_to_member(session, member.id)
            if not crew_member:
                return None, f"{member.name} does not exist in our database"

            stmt = select(TournamentParticipants).where(
                TournamentParticipants.user_id == crew_member.id,
                TournamentParticipants.tournament_id == tournament.id
            )
            is_participant = session.scalars(stmt).first()
            if is_participant:
                return tournament, f"{member.name} is already signed up for tournament: {tournament.name}"

            try:
                new_participant_object = challonge.participants.create(
                    slug, crew_member.username)
                player_challonge_id = int(
                    new_participant_object["id"])  # type: ignore

            except challonge.api.ChallongeException as e:
                return tournament, f"Unable to add '{member.name}' as a participant. Reason: \n{e}"

            new_participant = TournamentParticipants(
                tournament_id=tournament.id,
                user_id=crew_member.id,
                challonge_id=player_challonge_id

            )
            session.add(new_participant)

            return tournament, f"{member.name} has been successfully added to tournament: {tournament.name}\nCheck out the bracket at: {tournament.url}"

    @app_commands.command(name="sign_up", description="Sign up for the current tournament")
    async def sign_up(self, interaction: discord.Interaction):
        if interaction.channel_id != int(SIGNUPS_CH):
            await interaction.response.send_message(
                embed=self.build_simple_embed(
                    "🚫 Wrong Channel",
                    f"Use this command in <#{SIGNUPS_CH}>.",
                    discord.Color.red(),
                ),
                ephemeral=True,
            )
            return

        member = interaction.user
        slug = self.current_tournament
        if not slug:
            await interaction.response.send_message(
                embed=self.build_simple_embed(
                    "ℹ️ Info",
                    "There is currently no tournament ongoing.",
                    discord.Color.blurple(),
                ),
                ephemeral=True,
            )
            return

        tournament, msg = await self.__add_player_to_tournament(member, slug)

        with Session() as session:
            tournament = self.__check_if_tournament(session, slug)

            # Log it
            await self._log_to_logs(
                title="📝 Sign Up",
                description=f"By: {interaction.user.mention} ({interaction.user.id})",
                fields={
                    "Result": msg,
                    "Tournament": tournament.name if tournament else slug,
                    "Bracket": tournament.url if tournament and tournament.url else "—",
                    "Channel": f"<#{interaction.channel_id}>",
                },
            )

            embed = discord.Embed(
                title="✅ Successfully Signed Up!",
                description=msg,
                color=discord.Color.green()
            )
            if tournament:
                embed.add_field(name="Tournament",
                                value=tournament.name, inline=True)
                if getattr(tournament, "url", None):
                    embed.add_field(
                        name="Bracket",
                        value=f"[View on Challonge]({tournament.url})",
                        inline=True
                    )
            embed.set_footer(text="Good luck, have fun!")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="add_participant", description="Manually add participants to the current tournament")
    @app_commands.default_permissions(administrator=True)
    async def add_participant(self, interaction: discord.Interaction, member: discord.Member):
        slug = slugify(self.current_tournament)
        if not slug:
            await interaction.response.send_message(
                embed=self.build_simple_embed(
                    "ℹ️ Info", "There is currently no tournament ongoing.", discord.Color.blurple()),
                ephemeral=True
            )
            return

        _tournament, msg = await self.__add_player_to_tournament(member, slug)
        await interaction.response.send_message(
            embed=self.build_simple_embed(
                "📝 Add Participant", f"{msg}", discord.Color.green()),
            ephemeral=True
        )

    @app_commands.command(name="unregister", description="withdraw from the current tournament")
    async def unregister(self, interaction: discord.Interaction):
        member = interaction.user
        slug = slugify(self.current_tournament)
        if not slug:
            await interaction.response.send_message(
                embed=self.build_simple_embed(
                    "ℹ️ Info", "There is currently no tournament ongoing.", discord.Color.blurple()),
                ephemeral=True
            )
            return

        msg = await self.__remove_player_from_tournament(member, slug)

        await interaction.response.send_message(
            embed=self.build_simple_embed(
                "🗑️ Unregister", msg, discord.Color.orange()),
            ephemeral=True
        )

    @app_commands.command(name="unregister_player", description="withdraw a player from the current tournament")
    @app_commands.default_permissions(administrator=True)
    async def unregister_player(self, interaction: discord.Interaction, member: discord.Member):
        slug = slugify(self.current_tournament)
        if not slug:
            await interaction.response.send_message(
                embed=self.build_simple_embed(
                    "ℹ️ Info", "There is currently no tournament ongoing.", discord.Color.blurple()),
                ephemeral=True
            )
            return

        msg = await self.__remove_player_from_tournament(member, slug)

        await interaction.response.send_message(
            embed=self.build_simple_embed(
                "🗑️ Unregister Player", msg, discord.Color.orange()),
            ephemeral=True
        )

    # Matches
    @app_commands.command(name="report_win", description="Report who won your match")
    async def report_score(self, interaction: discord.Interaction, winner: discord.Member, video_link: str):
        if interaction.channel_id != int(REPORTS_CH):
            await interaction.response.send_message(
                embed=self.build_simple_embed(
                    "🚫 Wrong Channel", f"Use this command in <#{REPORTS_CH}>.", discord.Color.red()),
                ephemeral=True
            )
            return

        if not video_link:
            await interaction.response.send_message(
                embed=self.build_simple_embed(
                    "❌ Missing Video", "Please provide a video link of the battle.", discord.Color.red()),
                ephemeral=True
            )
            return
        
        if not validators.url(video_link):
            await interaction.response.send_message(
                embed=self.build_simple_embed(
                    "❌ Invalid Link",
                    "Please provide a valid http/https video URL.\n"
                    "Examples:\n• https://youtu.be/xxxx\n• https://streamable.com/xxxx\n• https://limewire.com/xxxx",
                    discord.Color.red()
                ),
                ephemeral=True
            )
            return

        slug = slugify(self.current_tournament)
        reporter_discord = interaction.user
        reporter_discord_id = reporter_discord.id
        winner_discord_id = winner.id

        with Session.begin() as session:
            tournament = self.__check_if_tournament(session, slug)
            if not tournament:
                await interaction.response.send_message(
                    embed=self.build_simple_embed(
                        "ℹ️ Info", "There is currently no tournament running.", discord.Color.blurple()),
                    ephemeral=True
                )
                return

            crew_member = discord_id_to_member(
                session, reporter_discord_id)
            winning_crew_member = discord_id_to_member(
                session, winner_discord_id)
            if not crew_member or not winning_crew_member:
                await interaction.response.send_message(
                    embed=self.build_simple_embed(
                        "❌ Error", "You are not registered in our database. Please contact management.", discord.Color.red()),
                    ephemeral=True
                )
                return

            participant = self.__check_if_participant(
                session, tournament.id, crew_member.id)
            winning_participant = self.__check_if_participant(
                session, tournament.id, winning_crew_member.id)
            if not participant or not winning_participant:
                await interaction.response.send_message(
                    embed=self.build_simple_embed(
                        "❌ Error", "You are not registered for this tournament.", discord.Color.red()),
                    ephemeral=True
                )
                return

            next_match_ch = self.__find_current_match_player(
                slug, participant.challonge_id)
            if not next_match_ch:
                await interaction.response.send_message(
                    embed=self.build_simple_embed(
                        "❌ Error", "No match could be found for this user.", discord.Color.red()),
                    ephemeral=True
                )
                return

            challonge_match_id = next_match_ch["id"]  # type: ignore
            player1_ch_id = next_match_ch["player1_id"] if next_match_ch["player1_id"] else None # type: ignore
            player2_ch_id = next_match_ch["player2_id"] if next_match_ch["player2_id"] else None # type: ignore
            round_match = next_match_ch["round"]  # type: ignore

            participant1 = self.__p_challonge_id_to_participant(
                session, tournament.id, player1_ch_id)
            participant2 = self.__p_challonge_id_to_participant(
                session, tournament.id, player2_ch_id)

            crew_member1 = self.__user_id_to_member(
                session, participant1.user_id)
            crew_member2 = self.__user_id_to_member(
                session, participant2.user_id)

            score = "1-0" if participant1 == winning_participant else "0-1"

            try:
                challonge.matches.update(
                    slug, challonge_match_id, scores_csv=score, winner_id=winning_participant.challonge_id)
            except challonge.api.ChallongeException as e:
                await interaction.response.send_message(
                    embed=self.build_simple_embed(
                        "❌ Unable to Update", f"{e}", discord.Color.red()),
                    ephemeral=True
                )
                return

            next_match_row = self.__get_match_row_by_chid(
                session, tournament.id, challonge_match_id)
            if not next_match_row:
                await interaction.response.send_message(
                    embed=self.build_simple_embed(
                        "❌ Error", "No match could be found.", discord.Color.red()),
                    ephemeral=True
                )
                return

            next_match_row.winner_participant_id = winning_participant.id
            next_match_row.score = score
            next_match_row.completed = True

            # Build the single embed
            announce = discord.Embed(
                title=f"🏆 Match Result Reported — Round {round_match}",
                description=f"**{crew_member1.username}** vs **{crew_member2.username}**",
                color=discord.Color.orange()
            )
            announce.add_field(name="Winner", value=winner.mention, inline=True)
            announce.add_field(name="Score", value=score, inline=True)
            announce.add_field(name="VOD", value=video_link, inline=False)
            if getattr(tournament, "url", None):
                announce.add_field(
                    name="Bracket", value=f"[View on Challonge]({tournament.url})", inline=False
                )

            # Send to logs channel
            try:
                log_ch = self.bot.get_channel(LOGS_CH) or await self.bot.fetch_channel(LOGS_CH)
                if log_ch:
                    await log_ch.send(embed=announce)
            except Exception:
                pass

            # Ephemeral confirmation to reporter
            await interaction.response.send_message(embed=announce, ephemeral=True)


    @app_commands.command(name="update_match", description="Update the score of a match")
    @app_commands.default_permissions(administrator=True)
    async def update_match(self, interaction: discord.Interaction, player1: discord.Member, player2: discord.Member, winner: discord.Member):
        slug = slugify(self.current_tournament)

        players = [player1.id, player2.id]
        if winner.id not in players:
            await interaction.response.send_message(
                embed=self.build_simple_embed(
                    "❌ Error", "Winner must be one of the two players.", discord.Color.red()),
                ephemeral=True
            )
            return

        with Session.begin() as session:
            tournament = self.__check_if_tournament(session, slug)
            if not tournament:
                await interaction.response.send_message(
                    embed=self.build_simple_embed(
                        "ℹ️ Info", "There is currently no tournament set as current tournament.", discord.Color.blurple()),
                    ephemeral=True
                )
                return

            crew_member1 = discord_id_to_member(session, player1.id)
            crew_member2 = discord_id_to_member(session, player2.id)
            winning_crew_member = discord_id_to_member(
                session, winner.id)

            if not crew_member1 or not crew_member2 or not winning_crew_member:
                await interaction.response.send_message(
                    embed=self.build_simple_embed(
                        "❌ Error", "One or more players do not exist in our database.", discord.Color.red()),
                    ephemeral=True
                )
                return

            participant1 = self.__check_if_participant(
                session, tournament.id, crew_member1.id)
            participant2 = self.__check_if_participant(
                session, tournament.id, crew_member2.id)
            winning_participant = self.__check_if_participant(
                session, tournament.id, winning_crew_member.id)

            if not participant1 or not participant2:
                await interaction.response.send_message(
                    embed=self.build_simple_embed(
                        "❌ Error", "One or more players are not part of this tournament.", discord.Color.red()),
                    ephemeral=True
                )
                return

            current_match = self.__get_match_row_for_players(
                session, tournament.id, participant1.id, participant2.id)
            if not current_match:
                await interaction.response.send_message(
                    embed=self.build_simple_embed(
                        "❌ Error", f"This match between **{player1.display_name}** and **{player2.display_name}** does not exist.", discord.Color.red()),
                    ephemeral=True
                )
                return

            score = "1-0" if winning_participant.id == current_match.participant1_id else "0-1"

            try:
                challonge.matches.update(
                    slug, current_match.challonge_id, scores_csv=score, winner_id=winning_participant.challonge_id)
                current_match.completed = True
                current_match.score = score
                current_match.winner_participant_id = winning_participant.id
                ok = await self.__prep_next_match_winner(session, slug, winning_participant.challonge_id)

            except challonge.api.ChallongeException as e:
                await interaction.response.send_message(
                    embed=self.build_simple_embed(
                        "❌ Update Failed", f"{e}", discord.Color.red()),
                    ephemeral=True
                )
                return

        msg = f"Match successfully updated. Winner: **{winner.display_name}**."
        if not ok:
            msg += "\n\n⚠️ Could not find and update winner’s next match."

        await interaction.response.send_message(
            embed=self.build_simple_embed(
                "✅ Match Updated", msg, discord.Color.green()),
            ephemeral=True
        )

    @app_commands.command(name="sync_db_to_challonge", description="Synchronize the Database to the bracket in Challonge for current tournament")
    @app_commands.default_permissions(administrator=True)
    async def sync_db_to_challonge(self, interaction: discord.Interaction):
        slug = slugify(self.current_tournament)

        with Session.begin() as session:
            tournament = self.__check_if_tournament(session, slug)
            if not tournament:
                await interaction.response.send_message(
                    embed=self.build_simple_embed(
                        "ℹ️ Info", "There is currently no tournament running.", discord.Color.blurple()),
                    ephemeral=True
                )
                return

            try:
                all_matches = challonge.matches.index(slug)
                for match in all_matches:
                    p1_challonge_id = match["player1_id"]  # type: ignore
                    p2_challonge_id = match["player2_id"]  # type: ignore
                    winner_challonge_id = match["winner_id"]  # type: ignore
                    score_challonge_match = match["scores_csv"]  # type: ignore

                    participant1 = self.__p_challonge_id_to_participant(
                        session, tournament.id, p1_challonge_id)
                    participant2 = self.__p_challonge_id_to_participant(
                        session, tournament.id, p2_challonge_id)
                    winning_participant = self.__p_challonge_id_to_participant(
                        session, tournament.id, winner_challonge_id
                    )

                    match_row = self.__get_match_row_by_chid(
                        session, tournament.id, match["id"])  # type: ignore
                    match_row.participant1_id = participant1.id if participant1 else None
                    match_row.participant2_id = participant2.id if participant2 else None
                    match_row.winner_participant_id = winning_participant.id if winning_participant else None
                    match_row.score = score_challonge_match if score_challonge_match else None

                    match_row.completed = True if match["state"] == "complete" else False # type: ignore

            except challonge.api.ChallongeException:
                await interaction.response.send_message(
                    embed=self.build_simple_embed(
                        "ℹ️ Info", "There is currently no tournament running.", discord.Color.blurple()),
                    ephemeral=True
                )
                return

        await interaction.response.send_message(
            embed=self.build_simple_embed(
                "🔄 Sync Complete", "Database synchronized with Challonge.", discord.Color.green()),
            ephemeral=True
        )

    async def check_if_match_exists(self, slug, round, discord_id_1, discord_id_2):
        with Session() as session:
            tournament = self.__check_if_tournament(session, slug)
            if not tournament:
                return False, "No tournament running right now"

            # Get Crew Members
            crew_member1 = discord_id_to_member(session, discord_id_1)
            crew_member2 = discord_id_to_member(session, discord_id_2)
            if not crew_member1 or not crew_member2:
                return False, "One or more players do not exist in our database."

            # Get Tournament Participant
            participant1 = self.__check_if_participant(
                session, tournament.id, crew_member1.id)
            participant2 = self.__check_if_participant(
                session, tournament.id, crew_member2.id)
            if not participant1 or not participant2:
                return False, f"One or more players are not participating in the current tournament."

            # Now get the match
            match = self.__get_match_row_for_players(
                session, tournament.id, participant1.id, participant2.id)
            if not match:
                return False, f"The match between {crew_member1.username} and {crew_member2.username}, does not exist for the current Tournament."

            if match.round != round:
                return False, f"That match exists, but it’s for round {match.round}, not round {round}."

            return True, "I found your match"

    async def post_schedule_embed(self, dt, player1, player2, round, schedule_channel, bracket_url):
        
        if dt < datetime.now(timezone.utc):
            return None

        unix_ts = int(dt.timestamp())
        embed = discord.Embed(
            title=f"📅 Match Scheduled — Round {round}",
            description=(
                f"{player1.mention} vs {player2.mention}\n\n"
                f"**Match Time:** <t:{unix_ts}:F>\n"
                f"**Relative:** <t:{unix_ts}:R>"
                # Clickable link for bracket url
            ),
            color=discord.Color.blurple()
        )
        if bracket_url:
            embed.description = (embed.description or "") + \
                f"\n\n**Bracket:** [View on Challonge]({bracket_url})"

        new_post = await schedule_channel.send(embed=embed)
        return new_post.id

    @app_commands.command(name="admin_schedule_match")
    @app_commands.default_permissions(administrator=True)
    async def admin_schedule_match(
            self,
            interaction: discord.Interaction,
            player1: discord.Member,
            player2: discord.Member,
            round: app_commands.Range[int, 1, 10],
            year: int,
            month: app_commands.Range[int, 1, 12],
            day: app_commands.Range[int, 1, 31],
            hour: app_commands.Range[int, 0, 23],
            minute: app_commands.Range[int, 0, 59]):

        # CODE START
        slug = slugify(self.current_tournament)
        discord_user1 = player1
        discord_user2 = player2
        schedule_channel = self.bot.get_channel(int(SCHEDULING_CH))

        ## GET TIMEZONE FROM USER

        if not interaction.guild:
            return

        if not slug:
            await interaction.response.send_message(
                embed=self.build_simple_embed(
                    "ℹ️ Info", "No tournament running right now.", discord.Color.blurple()),
                ephemeral=True
            )
            return

        match_exists, msg = await self.check_if_match_exists(slug, round, discord_user1.id, discord_user2.id)
        if not match_exists:
            await interaction.response.send_message(
                embed=self.build_simple_embed(
                    "❌ Error", msg, discord.Color.red()),
                ephemeral=True
            )
            return
        
        with Session.begin() as session:
            crew_member = discord_id_to_member(session, interaction.user.id)
            if not crew_member:
                return

            country_member = crew_member.country
            if not country_member:
                await interaction.response.send_message(f"Your country value is not set. Please contact management")
                return
        

            timezone_member = crew_member.timezone_name
            if not timezone_member:
                timezone_member = country_to_timezone(country_member)

            if not timezone_member:
                return
            
            tz = ZoneInfo(timezone_member)

            dt = datetime(
            year=year,
            month=month,
            day=day,
            hour=hour,
            minute=minute,
            tzinfo=tz)

            dt_utc = dt.astimezone(timezone.utc)

            # Other logic
            bracket_url = f"https://challonge.com/{slug}"
            new_post_id = await self.post_schedule_embed(dt_utc, discord_user1, discord_user2, round, schedule_channel, bracket_url)
            if not new_post_id:
                await interaction.response.send_message(
                    embed=self.build_simple_embed(
                        "❌ Error", "You cannot schedule a match in the past.", discord.Color.red()),
                    ephemeral=True
                )
                return

            post_url = f"https://discord.com/channels/{interaction.guild.id}/{schedule_channel.id}/{new_post_id}"

            await interaction.response.send_message(
                embed=self.build_simple_embed(
                    "✅ Match Scheduled", f"[View post here]({post_url})", discord.Color.green()),
                ephemeral=True
            )

    @app_commands.command(name="schedule_match", description="Schedule your match and post it to the scheduling channel")
    async def schedule_match(
            self,
            interaction: discord.Interaction,
            opponent: discord.Member,
            round: app_commands.Range[int, 1, 10],
            year: int,
            month: app_commands.Range[int, 1, 12],
            day: app_commands.Range[int, 1, 31],
            hour: app_commands.Range[int, 0, 23],
            minute: app_commands.Range[int, 0, 59]):
        
                # CODE START
        slug = slugify(self.current_tournament)
        discord_user1 = interaction.user
        discord_user2 = opponent
        schedule_channel = self.bot.get_channel(int(SCHEDULING_CH))
        if not interaction.guild:
            return
        
        if not slug:
            await interaction.response.send_message(
                embed=self.build_simple_embed(
                    "ℹ️ Info", "No tournament running right now.", discord.Color.blurple()),
                ephemeral=True
            )
            return
        
        match_exists, msg = await self.check_if_match_exists(slug, round, discord_user1.id, discord_user2.id)
        if not match_exists:
            await interaction.response.send_message(
                embed=self.build_simple_embed(
                    "❌ Error", msg, discord.Color.red()),
                ephemeral=True
            )
            return
        
        with Session.begin() as session:
            tournament = self.__check_if_tournament(session, slug)
            if not tournament:
                await interaction.response.send_message(
                embed=self.build_simple_embed(
                    "ℹ️ Info", "No tournament running now.", discord.Color.blurple()),
                ephemeral=True
                )
                return


            crew_member = discord_id_to_member(session, interaction.user.id)

            member1 = discord_id_to_member(session, discord_user1.id)
            member2 = discord_id_to_member(session, discord_user2.id)
            if not member1 or not member2:
                await interaction.response.send_message(
                embed=self.build_simple_embed(
                    "❌ Error", "Either 1 or both members or not registered in the database", discord.Color.red()),
                ephemeral=True
                )
                return
                
            p1 = self.__check_if_participant(session, tournament.id, member1.id)
            p2 = self.__check_if_participant(session, tournament.id, member2.id)

            if not p1 or not p2:
                await interaction.response.send_message(
                embed=self.build_simple_embed(
                    "❌ Error", f"Either 1 or both players are not registered for this tournament.\n\nPlayer1: {p1}\nPlayer2: {p2}", discord.Color.red()),
                ephemeral=True
                )
                return
            
            match_row = self.__get_match_row_for_players(session, tournament.id, p1.id, p2.id)
            if not match_row:
                await interaction.response.send_message(
                embed=self.build_simple_embed(
                    "❌ Error", "No match exists for both players combined.", discord.Color.red()),
                ephemeral=True
                )
                return
           
            if not crew_member:
                await interaction.response.send_message(
                    embed=self.build_simple_embed(
                        "❌ Error", "You are not registered in our database. Please contact management.", discord.Color.red()),
                    ephemeral=True
                )
                return
            
            country_member = crew_member.country
            if not country_member:
                await interaction.response.send_message(f"Your country value is not set. Please contact management")
                return
        

            timezone_member = crew_member.timezone_name
            if not timezone_member:
                timezone_member = country_to_timezone(country_member)
                await interaction.response.send_message(
                    embed=self.build_simple_embed(
                        "❌ Error", "NO TIMEZONE SET", discord.Color.red()),
                    ephemeral=True
                )
                return
            
            tz = ZoneInfo(timezone_member)

            dt = datetime(
            year=year,
            month=month,
            day=day,
            hour=hour,
            minute=minute,
            tzinfo=tz)

            dt_utc = dt.astimezone(timezone.utc)

            player1_id = match_row.participant1_id
            player2_id = match_row.participant2_id

            player1 = self.__get_participant_from_id(session, player1_id)
            player2 = self.__get_participant_from_id(session, player2_id)
            if not player1 or not player2:
                await interaction.response.send_message(
                    embed=self.build_simple_embed(
                        "❌ Error", f"NOT PLAYER 1: {player1}\nNOT PLAYER2: {player2}", discord.Color.red()),
                    ephemeral=True
                )
                return

            crew_member1 = self.__user_id_to_member(session, player1.user_id)
            crew_member2 = self.__user_id_to_member(session, player2.user_id)
            if not crew_member1 or not crew_member2:
                await interaction.response.send_message(
                    embed=self.build_simple_embed(
                        "❌ Error", f"NOT CREW_MEMBER1 {crew_member1}\nNOT CREW_MEMBER2: {crew_member2}\n\n{player1}\n{player2}", discord.Color.red()),
                    ephemeral=True
                )
                return
            
            discord_user1 = interaction.guild.get_member(crew_member1.discord_id)
            discord_user2 = interaction.guild.get_member(crew_member2.discord_id)
            if not discord_user1 or not discord_user2:
                await interaction.response.send_message(
                    embed=self.build_simple_embed(
                        "❌ Error", f"NOT DISCORD_USER1: {discord_user1}\nNOT DISCORD_USER2: {discord_user2}", discord.Color.red()),
                    ephemeral=True
                )
                return
            
            match_row.scheduled_datetime = dt_utc

            bracket_url = f"https://challonge.com/{slug}"

            new_post_id = await self.post_schedule_embed(dt_utc, discord_user1, discord_user2, round, schedule_channel, bracket_url)
            
            if not new_post_id:
                await interaction.response.send_message(
                    embed=self.build_simple_embed(
                        "❌ Error", "You cannot schedule a match in the past.", discord.Color.red()),
                    ephemeral=True
                )
                return

            post_url = f"https://discord.com/channels/{interaction.guild.id}/{schedule_channel.id}/{new_post_id}"
            
            await interaction.response.send_message(
                embed=self.build_simple_embed("✅ Match scheduled!", f"[View post here]({post_url})\n\ndt utc: {dt_utc}, match_row: {match_row}", discord.Color.green()), ephemeral=True
            )



    @app_commands.command(name="find_current_match", description="Find the details of your current tournament match")
    async def find_current_match(self, interaction: discord.Interaction):
        if interaction.guild_id != int(GUILD_ID):
            await interaction.response.send_message("You cannot use this command from this server/chat")
            return

        slug = slugify(self.current_tournament)
        discord_user = interaction.user

        if not slug:
            await interaction.response.send_message(
                embed=self.build_simple_embed(
                    "ℹ️ Info", "No tournament running right now.", discord.Color.blurple()),
                ephemeral=True
            )
            return

        # Discord_id -> Participant_id
        with Session() as session:
            crew_member = discord_id_to_member(session, discord_user.id)
            if not crew_member:
                await interaction.response.send_message(
                    embed=self.build_simple_embed(
                        "❌ Error", "You are not registered in our database. Please contact management.", discord.Color.red()),
                    ephemeral=True
                )
                return
            
            tournament = self.__check_if_tournament(session, slug)
            if not tournament:
                await interaction.response.send_message(
                    embed=self.build_simple_embed(
                        "ℹ️ Info", "There is currently no tournament running.", discord.Color.blurple()),
                    ephemeral=True
                )
                return
            
            if not tournament.ongoing:
                await interaction.response.send_message(
                    embed=self.build_simple_embed(
                        "ℹ️ Info", f"The current tournament hasn't started yet.\nCurrent tournament: {tournament.name}", discord.Color.red()),
                    ephemeral=True
                )
                return
            
            tournament_participant = self.__check_if_participant(
                session, tournament.id, crew_member.id)
            if not tournament_participant:
                await interaction.response.send_message(
                    embed=self.build_simple_embed(
                        "ℹ️ Info", f"You can't use this commands\nReason: You are not registered for tournament {tournament.name}", discord.Color.blurple()),
                    ephemeral=True
                )
                return

            tournament_match_chall = self.__find_next_match_player(
                slug, tournament_participant.challonge_id)
            if not tournament_match_chall:
                # No match for player
                await interaction.response.send_message(
                    embed=self.build_simple_embed(
                        "ℹ️ Info", f"No match found on challonge for {crew_member.id}", discord.Color.red()),
                    ephemeral=True
                )
                return

            match_id_challonge = tournament_match_chall["id"] if tournament_match_chall else None # type: ignore
            if not match_id_challonge:
                # no challonge id for match
                await interaction.response.send_message(
                    embed=self.build_simple_embed(
                        "❌ Error", "No ID found for this match on Challonge", discord.Color.red()),
                    ephemeral=True
                )
                return

            db_match_row = self.__get_match_row_by_chid(
                session, tournament.id, match_id_challonge)
            if not db_match_row:
                # no record in db of that match
                await interaction.response.send_message(
                    embed=self.build_simple_embed(
                        "❌ Error", "No record of this challonge match in our database.", discord.Color.red()),
                    ephemeral=True
                )
                return

            crew_member1 = None
            crew_member2 = None

            player1_id = db_match_row.participant1_id
            player1 = self.__get_participant_from_id(session, player1_id)
            if not player1:
                # No player 1 in that match
                player1 = None
            else:
                crew_member1 = self.__user_id_to_member(
                    session, player1.user_id)

            player2_id = db_match_row.participant2_id
            player2 = self.__get_participant_from_id(session, player2_id)
            if not player2:
                # No player 2 in that match
                player2 = None
            else:
                crew_member2 = self.__user_id_to_member(
                    session, player2.user_id)

            username_player1 = crew_member1.username if crew_member1 else None
            username_player2 = crew_member2.username if crew_member2 else None

            match_round = db_match_row.round
            opponent_username = username_player1 if username_player1 != crew_member.username else username_player2
            
            desc_lines = []
            if match_round is not None:
                desc_lines.append(f"**Round:** {match_round}")

            desc_lines.append(f"**Opponent:** {opponent_username}")

            # Build description text
            description = "\n".join(desc_lines)

            # Append bracket if available (clean clickable link)
            if getattr(tournament, "url", None):
                description += f"\n\n**Bracket:** [View on Challonge]({tournament.url})"

            dt = db_match_row.scheduled_datetime
            if dt and opponent_username:
                ts = int(dt.timestamp())  # unix epoch
                # :F = full date/time, :R = relative (e.g., "in 2 hours")
                description += f"\n\n**Scheduled:** <t:{ts}:F> • <t:{ts}:R>"
            else:
                description += "\n\n💡 Use `/schedule_match` to post your match time in the scheduling channel."



            embed = discord.Embed(
                title="🎯 Your Current Match",
                description=description,
                color=discord.Color.blurple()
            )
            embed.timestamp = discord.utils.utcnow()

            await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Tournaments(bot))
