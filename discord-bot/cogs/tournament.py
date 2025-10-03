import challonge.api
import discord
import os
import challonge
import requests
import sqlalchemy as sa

from discord import app_commands
from discord.ext import commands
from sqlalchemy import select
from database.database import Session
from database.models import Tournament, User, TournamentParticipants, TournamentMatches

# Global Variable
USERNAME = os.getenv("CH_USERNAME")
API_KEY = os.getenv("CH_API_KEY")

SIGNUPS_CH = int(os.getenv("SIGNUPS_CH_ID", 0))
REPORTS_CH = int(os.getenv("REPORTS_CH_ID", 0))
VIDEO_CHANNEL = int(os.getenv("VIDEO_CH_ID", 0))
ANNOUNCEMENT_CH = int(os.getenv("ANNOUNCEMENTS_CH_ID", 0))
LOGS_CH = int(os.getenv("LOGS_CH_ID", 0))


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
    def __check_if_tournament(session, slug):
        stmt = select(Tournament).where(Tournament.slug == slug)
        return session.scalars(stmt).first()

    @staticmethod
    def __get_challonge_id(slug):
        tournament = challonge.tournaments.show(slug)
        tournament_id = tournament["id"]  # type: ignore
        return tournament_id if tournament_id else None

    @staticmethod
    def __discord_id_to_member(session, discord_id):
        stmt = select(User).where(User.discord_id == discord_id)
        return session.scalars(stmt).first()

    @staticmethod
    def __participant_to_member(session, user_id):
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
    def __get_match_row_by_chid(session, tournament_id: int, match_chid: int):
        stmt = select(TournamentMatches).where(
            TournamentMatches.tournament_id == tournament_id,
            TournamentMatches.challonge_id == match_chid,
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
        logs_channel = 1423723506914295858
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
                await interaction.response.send_message(f"Tournament with name '{name}' does not exist.", ephemeral=True)
                return

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
            await interaction.response.send_message(f"I am currently not managing any tournament", ephemeral=True)
            return

        session = Session()
        with session:
            tournament = self.__check_if_tournament(
                session, current_tournament_slug)
            if not tournament:
                await interaction.response.send_message(f"The tournament im managing doesn't exist: '{current_tournament_slug}'", ephemeral=True)
                return

            tournament_summary = str(tournament)
            await interaction.response.send_message(tournament_summary, ephemeral=True)

    @app_commands.command(name="create_tournament", description="Create tournament of Challonge")
    @app_commands.default_permissions(administrator=True)
    async def create_tournament(self, interaction: discord.Interaction, name: str):
        slug = slugify(name)

        with Session.begin() as session:
            existing_tournament = self.__check_if_tournament(session, slug)
            if existing_tournament:
                await interaction.response.send_message(f"Could not create tournament, because:\nTournament already exists", ephemeral=True)
                return

            try:
                challonge.tournaments.create(
                    name=name,
                    url=slug,
                    tournament_type="single elimination",
                    hold_third_place_match=True
                )

            except challonge.api.ChallongeException as e:
                await interaction.response.send_message(f"Could not create tournament because:\n{e}", ephemeral=True)
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

        await interaction.response.send_message(f"Tournament: '{slug}' successfully created\nSee bracket at {tournament_url}", ephemeral=True)

    @app_commands.command(name="delete_tournament", description="Delete an existing tournament")
    @app_commands.default_permissions(administrator=True)
    async def delete_tournament(self, interaction: discord.Interaction, name: str):
        slug = slugify(name)
        with Session.begin() as session:
            tournament = self.__check_if_tournament(session, slug)
            if not tournament:
                await interaction.response.send_message(f"Tournament '{slug}' does not exist.", ephemeral=True)
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

        msg = f"Tournament '{deleted_tournament_slug}' deleted"
        if remote_delete_error_msg:
            msg = msg + "\nCould not delete remote. Reason: \n" + remote_delete_error_msg

        await interaction.response.send_message(msg, ephemeral=True)

    @app_commands.command(name="start_tournament", description="Start a specific tournament")
    @app_commands.default_permissions(administrator=True)
    async def start_tournament(self, interaction: discord.Interaction, name: str):
        slug = slugify(name)
        with Session.begin() as session:
            tournament = self.__check_if_tournament(session, slug)
            if not tournament:
                await interaction.response.send_message(f"Tournament '{name}' does not exist", ephemeral=True)
                return

            if tournament.ongoing:
                await interaction.response.send_message(f"Tournament '{name}' is already ongoing", ephemeral=True)
                return

            try:
                challonge.participants.randomize(slug)
                challonge.tournaments.start(slug)
            except challonge.api.ChallongeException as e:
                await interaction.response.send_message(f"Could not start tournament. Reason: \n{e}", ephemeral=True)
                return

            error_message = None

            try:
                tournament_matches = challonge.matches.index(slug)
                await self.insert_matches_in_db(session, tournament_matches, tournament)
            except challonge.api.ChallongeException as e:
                error_message = str(e)

            tournament.ongoing = True
            msg = f"Tournament '{name}' has now started"

            if error_message:
                msg = msg + " \n" + error_message

        await interaction.response.send_message(msg, ephemeral=True)

    @app_commands.command(name="end_tournament", description="End a specific ongoing tournament")
    @app_commands.default_permissions(administrator=True)
    async def end_tournament(self, interaction: discord.Interaction):
        slug = slugify(self.current_tournament)

        try:
            challonge.tournaments.finalize(slug)
        except challonge.api.ChallongeException as e:
            await interaction.response.send_message(f"Could not end this tournament because: \n{e}", ephemeral=True)
            return

        with Session.begin() as session:

            tournament = self.__check_if_tournament(session, slug)
            if not tournament:
                await interaction.response.send_message(f"There is currently no tournament running.", ephemeral=True)
                return

            challonge_winner_id = self.get_participant_on_rank(slug, 1)
            if not challonge_winner_id:
                await interaction.response.send_message(f"No winner available. Tournament hasn't been finalized", ephemeral=True)
                return

            participant_winner = self.__p_challonge_id_to_participant(
                session, tournament.id, challonge_winner_id)
            if not participant_winner:
                await interaction.response.send_message(f"Winner is not registered as a participant.", ephemeral=True)
                return

            crew_member = self.__participant_to_member(
                session, participant_winner.id)
            if not crew_member:
                await interaction.response.send_message(f"winner does not exist in our database.", ephemeral=True)
                return

            tournament.winner_id = crew_member.id
            tournament.ongoing = False
            self.current_tournament = None
            await interaction.response.send_message(f"Tournament '{tournament.name}' has ended. Winner: {crew_member.username}\nCheck bracket at: {tournament.url}", ephemeral=True)

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

            crew_member = self.__discord_id_to_member(session, member.id)
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

            crew_member = self.__discord_id_to_member(session, member.id)
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
            await interaction.response.send_message(f"You are only allowed to use this command in the <#{SIGNUPS_CH}> channel.", ephemeral=True)
            return

        member = interaction.user
        slug = self.current_tournament
        if not slug:
            await interaction.response.send_message(f"There is currently no tournament ongoing", ephemeral=True)
            return

        tournament, msg = await self.__add_player_to_tournament(member, slug)

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
            embed.add_field(name="Tournament", value=tournament.name, inline=True)
            if getattr(tournament, "challonge_link", None):
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
            await interaction.response.send_message(f"There is currently no tournament ongoing", ephemeral=True)
            return

        msg = await self.__add_player_to_tournament(member, slug)
        await interaction.response.send_message(msg, ephemeral=True)

    @app_commands.command(name="unregister", description="withdraw from the current tournament")
    async def unregister(self, interaction: discord.Interaction):
        member = interaction.user
        slug = slugify(self.current_tournament)
        if not slug:
            await interaction.response.send_message(f"There is currently no tournament ongoing", ephemeral=True)
            return

        msg = await self.__remove_player_from_tournament(member, slug)

        await interaction.response.send_message(msg, ephemeral=True)

    @app_commands.command(name="unregister_player", description="withdraw a player from the current tournament")
    @app_commands.default_permissions(administrator=True)
    async def unregister_player(self, interaction: discord.Interaction, member: discord.Member):
        slug = slugify(self.current_tournament)
        if not slug:
            await interaction.response.send_message(f"There is currently no tournament ongoing", ephemeral=True)
            return

        msg = await self.__remove_player_from_tournament(member, slug)

        await interaction.response.send_message(msg, ephemeral=True)

    # Matches
    @app_commands.command(name="report_win", description="Report who won your match")
    async def report_score(self, interaction: discord.Interaction, winner: discord.Member, video_link: str):
        if interaction.channel_id != int(REPORTS_CH):
            await interaction.response.send_message(F"You are only allowed to use this command in the <#{REPORTS_CH}>", ephemeral=True)
            return

        if not video_link:
            await interaction.response.send_message(F"No Video link provided. Please provide a video link of the battle.", ephemeral=True)
            return

        slug = slugify(self.current_tournament)
        reporter_discord = interaction.user
        reporter_discord_id = reporter_discord.id
        winner_discord_id = winner.id

        with Session.begin() as session:
            tournament = self.__check_if_tournament(session, slug)
            if not tournament:
                await interaction.response.send_message("There is currently no tournament running.", ephemeral=True)
                return

            crew_member = self.__discord_id_to_member(
                session, reporter_discord_id)
            winning_crew_member = self.__discord_id_to_member(
                session, winner_discord_id)
            if not crew_member or not winning_crew_member:
                await interaction.response.send_message("You are not registered in our database. Please contact management", ephemeral=True)
                return

            participant = self.__check_if_participant(
                session, tournament.id, crew_member.id)
            winning_participant = self.__check_if_participant(
                session, tournament.id, winning_crew_member.id)
            if not participant or not winning_participant:
                await interaction.response.send_message("You are not registered for this tournament", ephemeral=True)
                return

            next_match_ch = self.__find_current_match_player(
                slug, participant.challonge_id)
            if not next_match_ch:
                await interaction.response.send_message("No match could be found for this user.", ephemeral=True)
                return

            challonge_match_id = next_match_ch["id"]  # type: ignore
            player1_ch_id = next_match_ch["player1_id"] if next_match_ch["player1_id"] else None # type: ignore
            player2_ch_id = next_match_ch["player2_id"] if next_match_ch["player2_id"] else None # type: ignore
            round_match = next_match_ch["round"]  # type: ignore

            participant1 = self.__p_challonge_id_to_participant(
                session, tournament.id, player1_ch_id)
            participant2 = self.__p_challonge_id_to_participant(
                session, tournament.id, player2_ch_id)

            crew_member1 = self.__participant_to_member(
                session, participant1.user_id)
            crew_member2 = self.__participant_to_member(
                session, participant2.user_id)

            score = "1-0" if participant1 == winning_participant else "0-1"

            try:
                challonge.matches.update(
                    slug, challonge_match_id, scores_csv=score, winner_id=winning_participant.challonge_id)
            except challonge.api.ChallongeException as e:
                await interaction.response.send_message(f"Unable to update the match. Reason: {e}", ephemeral=True)
                return

            next_match_row = self.__get_match_row_by_chid(
                session, tournament.id, challonge_match_id)
            if not next_match_row:
                await interaction.response.send_message(f"No Match could be found.", ephemeral=True)
                return

            next_match_row.winner_participant_id = winning_participant.id
            next_match_row.score = score
            next_match_row.completed = True

            # Embed to Video Channel
            video_ch = self.bot.get_channel(VIDEO_CHANNEL) or await self.bot.fetch_channel(VIDEO_CHANNEL)
            if video_ch:
                announce = discord.Embed(
                    title=f"🏆 Match Result Reported — Round {round_match}",
                    description=f"**{crew_member1.username}** vs **{crew_member2.username}**",
                    color=discord.Color.orange()
                )
                announce.add_field(name="Winner", value=winner.mention, inline=True)
                announce.add_field(name="VOD", value=video_link, inline=True)
                if getattr(tournament, "challonge_link", None):
                    announce.add_field(name="Bracket", value=f"[View on Challonge]({tournament.url})", inline=False)
                await video_ch.send(embed=announce)
            
            # Log in
            try:
                await self._log_to_logs(
                    title="🏆 Report Win",
                    description=f"By: {reporter_discord.mention} ({reporter_discord.id})",
                    fields={
                        "Tournament": tournament.name,
                        "Bracket": (tournament.url or "—"),
                        "Round": str(round_match),
                        "Match": f"{crew_member1.username} vs {crew_member2.username}",
                        "Winner": winner.mention,
                        "VOD": video_link,
                        "Channel": f"<#{interaction.channel_id}>",
                    },
                )
            except Exception:
                pass

            # Nice ephemeral confirmation to the reporter
            confirm = discord.Embed(
                title="✅ Score Submitted",
                description=f"Round **{round_match}** has been updated.",
                color=discord.Color.green()
            )
            confirm.add_field(name="Match", value=f"{crew_member1.username} vs {crew_member2.username}", inline=False)
            confirm.add_field(name="Winner", value=winner.mention, inline=True)
            confirm.add_field(name="Score", value=score, inline=True)
            confirm.add_field(name="VOD", value=video_link, inline=False)
            if getattr(tournament, "challonge_link", None):
                confirm.add_field(name="Bracket", value=f"[View on Challonge]({tournament.url})", inline=False)
                    
            await interaction.response.send_message(embed=confirm, ephemeral=True)

    @app_commands.command(name="update_match", description="Update the score of a match")
    @app_commands.default_permissions(administrator=True)
    async def update_match(self, interaction: discord.Interaction, player1: discord.Member, player2: discord.Member, winner: discord.Member):
        slug = slugify(self.current_tournament)

        players = [player1.id, player2.id]
        if winner.id not in players:
            await interaction.response.send_message("Winner must be one of the two players.", ephemeral=True)
            return

        with Session.begin() as session:
            tournament = self.__check_if_tournament(session, slug)
            if not tournament:
                await interaction.response.send_message(f"There is currently no tournament set as current tournament", ephemeral=True)
                return

            crew_member1 = self.__discord_id_to_member(session, player1.id)
            crew_member2 = self.__discord_id_to_member(session, player2.id)
            winning_crew_member = self.__discord_id_to_member(
                session, winner.id)

            if not crew_member1 or not crew_member2:
                await interaction.response.send_message(f"1 or more players do not exist in our database", ephemeral=True)
                return

            participant1 = self.__check_if_participant(
                session, tournament.id, crew_member1.id)
            participant2 = self.__check_if_participant(
                session, tournament.id, crew_member2.id)
            winning_participant = self.__check_if_participant(
                session, tournament.id, winning_crew_member.id)

            if not participant1 or not participant2:
                await interaction.response.send_message(f"1 or more players are not part of this Tournament", ephemeral=True)
                return

            current_match = self.__get_match_row_for_players(
                session, tournament.id, participant1.id, participant2.id)
            if not current_match:
                await interaction.response.send_message(f"This match between '{player1.display_name}' and '{player2.display_name}' does not exist.", ephemeral=True)
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
                await interaction.response.send_message(f"Something went wrong. Error: {e}", ephemeral=True)
                return

        msg = f"Match successfully update with winner: {winner.display_name}"
        if not ok:
            msg = msg + "\n" + "ERROR! Could not find and update next match of winner."

        await interaction.response.send_message(msg, ephemeral=True)

    @app_commands.command(name="sync_db_to_challonge", description="Synchronize the Database to the bracket in Challonge for current tournament")
    @app_commands.default_permissions(administrator=True)
    async def sync_db_to_challonge(self, interaction: discord.Interaction):
        slug = slugify(self.current_tournament)
        msg = ""

        with Session.begin() as session:
            tournament = self.__check_if_tournament(session, slug)
            if not tournament:
                await interaction.response.send_message(f"There is currently no tournament running", ephemeral=True)
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

                    msg = f"Database successfully synchronized with the Challonge Tournament Bracket."

            except challonge.api.ChallongeException:
                await interaction.response.send_message(f"There is currently no tournament running", ephemeral=True)
                return

        msg = f"Database synchronized.\n"

        await interaction.response.send_message(msg, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Tournaments(bot))
