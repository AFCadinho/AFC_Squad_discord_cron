import challonge.api
import discord
import os
import challonge
import requests
import sqlalchemy as sa
import validators
import logging

from datetime import datetime, timezone
from discord import app_commands
from discord.ext import commands
from sqlalchemy import select, func
from sqlalchemy.orm import aliased
from database.database import Session
from database.models import Tournament, User, TournamentParticipants, TournamentMatches
from helpers import country_to_timezone, discord_id_to_member, participant_id_to_member, log_command_error, create_new_round_message, create_winner_message, ChannelFactory, ChannelManager, ChannelDestroyer
from zoneinfo import ZoneInfo
from typing import Any, Dict, Optional
from random import choice


# Global Variable
USERNAME = os.getenv("CH_USERNAME")
API_KEY = os.getenv("CH_API_KEY")
GUILD_ID = os.getenv("GUILD_ID", 0)

SIGNUPS_CH = int(os.getenv("SIGNUPS_CH_ID", 0))
REPORTS_CH = int(os.getenv("REPORTS_CH_ID", 0))
VIDEO_CHANNEL = int(os.getenv("VIDEO_CH_ID", 0))
ANNOUNCEMENT_CH = int(os.getenv("ANNOUNCEMENTS_CH_ID", 0))
STAFF_ANNOUNCEMENT_CH = int(os.getenv("STAFF_ANNOUNCEMENTS_CH_ID", 0))
LOGS_CH = int(os.getenv("LOGS_CH_ID", 0))
SCHEDULING_CH = int(os.getenv("SCHEDULING_CH_ID", 0))

REWARDS_CATEGORY = int(os.getenv("REWARDS_CAT_ID", 0))
MATCHES_CATEGORY = int(os.getenv("MATCHES_CAT_ID", 0))

log = logging.getLogger(__name__)


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


def fetch_current_round():
    with Session.begin() as session:
        stmt = select(TournamentMatches.round).join(
            Tournament, Tournament.id == TournamentMatches.tournament_id).where(
                TournamentMatches.completed == False,
                Tournament.current_tournament == True,
                TournamentMatches.round > 0
        )

        matches = session.scalars(stmt).all()
        if not matches:
            return None

        lowest_round = min(matches)

        return lowest_round


def fetch_max_round():
    with Session.begin() as session:
        stmt = select(func.max(TournamentMatches.round)).join(
            Tournament, Tournament.id == TournamentMatches.tournament_id
        ).where(
            Tournament.current_tournament.is_(True),
            TournamentMatches.round > 0
        )
        return session.scalar(stmt)


def slugify(string) -> str | None:
    if not string:
        return None
    return string.replace(" ", "_").lower()


class Tournaments(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        auth_tournament()
        self.current_tournament = fetch_current_tournament()
        self.current_round = fetch_current_round()
        self.max_round = fetch_max_round()
        self.channel_factory = ChannelFactory(bot)
        self.channel_manager = ChannelManager(bot)
        self.channel_destroyer = ChannelDestroyer(bot)

    # Static Methods ---------------------------------
    @staticmethod
    def __get_final_match(session, tournament_id, tournament_round, limit=1):
        stmt = (
                select(TournamentMatches)
                .where(
                    TournamentMatches.tournament_id == tournament_id,
                    TournamentMatches.round == tournament_round,
                    TournamentMatches.completed.is_(True)
                )
            )
        return session.scalars(stmt).first()
    
    @staticmethod
    def __check_uncompleted_matches(session, tournament_id: int, current_round: int):

        stmt = (
            select(TournamentMatches)
            .where(
                TournamentMatches.tournament_id == tournament_id,
                TournamentMatches.completed.is_(False),
                TournamentMatches.round == current_round
            )
        )
        return session.scalars(stmt).all()

    @staticmethod
    def __winner_reported(discord_id1, discord_id2, discord_id_winner) -> bool:

        discord_users = [discord_id1, discord_id2]
        if discord_id_winner not in discord_users:
            return False
        return True

    @staticmethod
    def __get_timezone_info(crew_member: User) -> ZoneInfo | None:
        country_member = crew_member.country
        if not country_member:
            return None

        timezone_member = crew_member.timezone_name
        if not timezone_member:
            timezone_member = country_to_timezone(country_member)

        if not timezone_member:
            return None

        return ZoneInfo(timezone_member)

    @staticmethod
    def __get_match_for_users(session, slug, match_round, discord_id, opponent_discord_id):

        log.info(
            f"""DEBUGGING get_match_for_users help:\nslug={slug}, round={match_round}, ids={discord_id}, {opponent_discord_id}""")

        p1 = aliased(TournamentParticipants)
        p2 = aliased(TournamentParticipants)
        u1 = aliased(User)
        u2 = aliased(User)

        stmt = (
            select(Tournament.url, p1, p2, TournamentMatches)
            .select_from(TournamentMatches)
            .join(Tournament, Tournament.id == TournamentMatches.tournament_id)
            .join(p1, p1.id == TournamentMatches.participant1_id)
            .join(p2, p2.id == TournamentMatches.participant2_id)
            .join(u1, u1.id == p1.user_id)
            .join(u2, u2.id == p2.user_id)
            .where(
                Tournament.slug == slug,
                Tournament.current_tournament.is_(True),
                TournamentMatches.round == match_round,
                sa.or_(
                    sa.and_(
                        u1.discord_id == discord_id,
                        u2.discord_id == opponent_discord_id
                    ),
                    sa.and_(
                        u1.discord_id == opponent_discord_id,
                        u2.discord_id == discord_id
                    )
                )
            )
            .limit(1)
        )
        return session.execute(stmt).first() or ()

    @staticmethod
    def __get_tournament_player(session, slug: str, discord_id: int):
        tour_stmt = (
            select(Tournament, TournamentParticipants)
            .join(TournamentParticipants, TournamentParticipants.tournament_id == Tournament.id)
            .join(User, TournamentParticipants.user_id == User.id)
            .where(
                Tournament.slug == slug,
                Tournament.current_tournament == True,
                User.discord_id == discord_id
            )
        )
        return session.execute(tour_stmt).first()

    @staticmethod
    def __get_match_tuple(session, challonge_match_id: int):
        p1 = aliased(TournamentParticipants)
        p2 = aliased(TournamentParticipants)

        stmt = (
            select(TournamentMatches, p1, p2).
            join(p1, p1.id == TournamentMatches.participant1_id).
            join(p2, p2.id == TournamentMatches.participant2_id).
            where(TournamentMatches.challonge_id == challonge_match_id)
        )
        return session.execute(stmt).first()

    @staticmethod
    def __get_match_participants(session, tournament_id, participant_id, round):
        p1 = aliased(TournamentParticipants)
        p2 = aliased(TournamentParticipants)

        stmt = (
            select(TournamentMatches, p1, p2)
            .join(p1, p1.id == TournamentMatches.participant1_id)
            .join(p2, p2.id == TournamentMatches.participant2_id)
            .where(
                TournamentMatches.tournament_id == tournament_id,
                TournamentMatches.round == round,
                sa.or_(
                    TournamentMatches.participant1_id == participant_id,
                    TournamentMatches.participant2_id == participant_id
                )
            )
        )

        return session.execute(stmt).first()

    @staticmethod
    def build_simple_embed(title: str, description: str, color: discord.Color):
        embed = discord.Embed(
            title=title,
            description=description,
            color=color)
        embed.timestamp = discord.utils.utcnow()
        return embed

    @staticmethod
    def __check_if_tournament(session, slug) -> Tournament:
        stmt = select(Tournament).where(Tournament.slug == slug)
        return session.scalars(stmt).first()

    @staticmethod
    def __get_challonge_id(slug):
        tournament = challonge.tournaments.show(slug)
        if not isinstance(tournament, Dict):
            return None

        tournament_id = tournament["id"]
        return tournament_id if tournament_id else None

    @staticmethod
    def __user_id_to_member(session, user_id) -> User:
        stmt = select(User).where(User.id == user_id)
        return session.scalars(stmt).first()

    @staticmethod
    def __check_if_participant(session, tournament_id, user_id) -> TournamentParticipants:
        stmt = select(TournamentParticipants).where(
            TournamentParticipants.user_id == user_id,
            TournamentParticipants.tournament_id == tournament_id)
        return session.scalars(stmt).first()

    @staticmethod
    def __get_match_row_for_players(session, tournament_id, p1_id, p2_id, only_unfinished=True):
        conditions = [
            TournamentMatches.tournament_id == tournament_id,
            sa.or_(
                sa.and_(
                    TournamentMatches.participant1_id == p1_id,
                    TournamentMatches.participant2_id == p2_id),

                sa.and_(
                    TournamentMatches.participant1_id == p2_id,
                    TournamentMatches.participant2_id == p1_id),
            )
        ]

        if only_unfinished:
            conditions.append(TournamentMatches.completed == False)
        
        stmt = select(TournamentMatches).where(*conditions)

        return session.scalars(stmt).first()

    @staticmethod
    def __get_match_row_by_chid(session, tournament_id: int, match_ch_id: int):
        stmt = select(TournamentMatches).where(
            TournamentMatches.tournament_id == tournament_id,
            TournamentMatches.challonge_id == match_ch_id,
        )
        return session.scalars(stmt).first()

    @staticmethod
    def __find_next_match_player(slug, player_challonge_id) -> dict[str, Any] | None:
        next_match = None
        try:
            player_matches = challonge.matches.index(
                slug, participant_id=player_challonge_id)
        except:
            return next_match

        for match in player_matches:
            if isinstance(match, Dict) and match["state"] != "complete":
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
            if isinstance(match, dict) and match["state"] == "open":
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
            if not isinstance(participant, Dict):
                return None

            participant_rank = participant["final_rank"]
            if participant_rank == rank:
                return participant["id"]

        return None

    @commands.Cog.listener()
    async def on_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        # Log to Discord
        await log_command_error(self.bot, interaction, error)

        # Give user a friendly message if not already replied
        if not interaction.response.is_done():
            await interaction.response.send_message(
                "⚠️ Something went wrong while running this command.",
                ephemeral=True
            )
        else:
            await interaction.followup.send(
                "⚠️ Something went wrong while running this command.",
                ephemeral=True
            )

    # HELPER FUNCTIONS
    async def get_match_for_discord_ids(self, session, tournament_id, discord_id1, discord_id2) -> TournamentMatches | None:
        crew_member1 = discord_id_to_member(session, discord_id1)
        crew_member2 = discord_id_to_member(session, discord_id2)
        
        if not crew_member1 or not crew_member2:
            log.info(f"FUNCTION: get_match_for_discord\n1 or more Discord Users are not crew members.\nDiscord User 1: {crew_member1}\nDiscord User2: {crew_member2}")
            return None

        participant1 = self.__check_if_participant(
                session, tournament_id, crew_member1.id)
        participant2 = self.__check_if_participant(
            session, tournament_id, crew_member2.id)

        if not participant1 or not participant2:
            log.info(f"FUNCTION: get_match_for_discord\n1 or more Crew members are not Participants.\nCrew Member 1: {participant1}\nCrew Member2: {participant2}")
            return None

        current_match = self.__get_match_row_for_players(
            session, tournament_id, participant1.id, participant2.id, only_unfinished=False)
        
        return current_match

    async def show_winner_details(self, guild, winner, video_link):
        staff_announcement_channel = guild.get_channel(STAFF_ANNOUNCEMENT_CH)

        if isinstance(staff_announcement_channel, discord.TextChannel):
            await staff_announcement_channel.send(
                f"🏁 **Tournament winner has been decided!**\n\n"
                f"**Winner:** {winner.username}\n"
                f"**VOD Link:** {video_link or 'N/A'}\n\n"
                f"🛠️ **Next steps**\n"
                f"• To change the VOD link, use `/edit_vod_link`\n"
                f"• To confirm the winner and generate the final announcement, use `/finalize_tournament`"
                f"@everyone"
            )

    async def update_discord_channels(self, current_round, guild: discord.Guild, winning_member, members: list):
        if len(members) != 2:
            log.info(f"FUNCTION: update_discord_channels\nERROR: The length of members is NOT 2.")
            return
        
        crew_member1 = members[0]
        crew_member2 = members[1]
        winning_crew_member = winning_member
        
        # Round Conditions
        slug = self.current_tournament
        is_semi_final = (self.max_round - current_round == 1)
        is_final = (self.max_round == current_round)
        is_bronze_match = (current_round == 0)
        slug = self.current_tournament

        if is_semi_final:
            pass
        elif is_bronze_match:
            log.info(f"This is a Bronze Match")
            await self.channel_factory.tournament_rewards(guild, [crew_member1, crew_member2], REWARDS_CATEGORY, slug)
        elif is_final:
            log.info(f"This is a Finals Match")
            await self.channel_factory.tournament_rewards(guild, [crew_member1, crew_member2], REWARDS_CATEGORY, slug)
        else:
            log.info(f"Not a Bronze Match")
            losing_crew_member = crew_member1 if crew_member1 != winning_crew_member else crew_member2
            await self.channel_factory.tournament_rewards(guild, [losing_crew_member], REWARDS_CATEGORY, slug)


    async def check_if_finished(self, session, current_match_row, guild: discord.Guild, winning_member, members: list):
        await self.update_discord_channels(current_match_row.round, guild, winning_member, members)

        uncompleted_matches = self.__check_uncompleted_matches(
            session, current_match_row.tournament_id, current_match_row.round)

        if len(uncompleted_matches) == 0:
            log.info(
                f"COMMAND: report_win\nThe current round is: {current_match_row.round}\nThe Max round is: {self.max_round}")
            # Semi Finals when bronze match needs to be created
            if self.max_round - current_match_row.round == 1:
                await self.channel_destroyer.delete_channels(guild, MATCHES_CATEGORY)
                await self._setup_bronze_match(session, current_match_row.tournament_id, guild)
                await self._setup_next_round(session, current_match_row.tournament_id, current_match_row.round, guild)

            # Finals or Bronze match
            elif current_match_row.round == self.max_round or current_match_row.round == 0:
                log.info(f"COMMAND: report_win\nBronze or Final Match detected. Checking if all matches are played...")
                if not await self.check_all_played(session, current_match_row.tournament_id):
                    log.info(f"COMMAND: report_win\nNot All Matches have been played yet.")
                    return False

                # Finalize tournament
                log.info(f"COMMAND: report_win\nAll Matches have been played. Setting up announcement")
                await self.show_winner_details(guild, winning_member, current_match_row.battle_url)
                # await self.finalize_tournament(session, tournament_id, guild)
                return True

            else:
                await self.channel_destroyer.delete_channels(guild, MATCHES_CATEGORY)
                await self._setup_next_round(session, current_match_row.tournament_id, current_match_row.round, guild)
                return False


    async def check_all_played(self, session, tournament_id):
        if not self.current_tournament:
            return

        stmt = (
            select(TournamentMatches)
            .where(
                TournamentMatches.tournament_id == tournament_id,
                TournamentMatches.completed.is_(False),
            )
        )
        unplayed_matches = session.scalars(stmt).all()
        return len(unplayed_matches) == 0

    async def _setup_bronze_match(self, session, tournament_id, guild: discord.Guild):
        if not guild or not self.current_tournament:
            return

        stmt = (
            select(TournamentMatches)
            .where(
                TournamentMatches.tournament_id == tournament_id,
                TournamentMatches.round == 0
            )
        )
        bronze_match = session.scalars(stmt).first()
        if not bronze_match:
            return

        user1 = participant_id_to_member(
            session, bronze_match.tournament_id, bronze_match.participant1_id)
        user2 = participant_id_to_member(
            session, bronze_match.tournament_id, bronze_match.participant2_id)
        if not user1 or not user2:
            log.info(f"FUNCTION: _setup_bronze_match\nDEBUG: user1: {user1}\nuser2: {user2}")
            return

        channel_name = await self.channel_factory.tournament_match(guild, [user1, user2], MATCHES_CATEGORY, bronze_match.round)
        return channel_name

    async def _setup_next_round(self, session, tournament_id, current_round, guild: discord.Guild):
        if not guild or not self.current_tournament or not self.max_round:
            log.info("FUNCTION: _setup_next_round\nERROR: Didn't pass first check")
            return
        if not isinstance(current_round, int):
            log.info(
                "FUNCTION: _setup_next_round\nError: current round is not an instance of type int")
            return

        next_round = current_round + 1

        # Fetch matches for next_round
        stmt = select(TournamentMatches).where(
            TournamentMatches.tournament_id == tournament_id,
            TournamentMatches.round == next_round
        )
        tournament_matches = session.scalars(stmt).all()

        if not tournament_matches:
            log.info(
                f"[next_round] No matches for round {next_round}; t_id={tournament_id}")
            return

        # Update state
        self.current_round = next_round
        log.info(
            f"FUNCTION: _setup_next_round\nself.current round is now: {self.current_round} ")

        created = 0
        for match in tournament_matches:
            user1 = participant_id_to_member(
                session, match.tournament_id, match.participant1_id)
            user2 = participant_id_to_member(
                session, match.tournament_id, match.participant2_id)
            if not user1 or not user2:
                log.info(
                    f"[next_round] Skipping match {match.challonge_id}: p1={match.participant1_id}, p2={match.participant2_id}")
                continue

            channel_name = await self.channel_factory.tournament_match(guild, [user1, user2], MATCHES_CATEGORY, match.round)
            if channel_name:
                created += 1

        if created:
            announcement_channel = guild.get_channel(ANNOUNCEMENT_CH)
            if isinstance(announcement_channel, discord.TextChannel):
                msg = create_new_round_message(
                    current_round, self.current_round, self.max_round, self.current_tournament)
                await announcement_channel.send(msg)
        else:
            log.info(
                f"[next_round] No channels created for round {next_round} (all matches skipped?)")

    async def _post_schedule_embed(self, dt, player1, player2, round, schedule_channel, bracket_url):

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

    async def __build_match_embed(self, tournament, match, p1, p2, requester_discord_id, interaction: discord.Interaction, session, admin=False) -> discord.Embed | None:
        player1 = p1
        player2 = p2
        participants = [player1, player2]

        discord_members = await self._crew_to_discord_member(session, interaction, participants)
        discord_user1 = discord_members[0]
        discord_user2 = discord_members[1]

        title = "🎯 Your Current Match" if not admin else "🛠️ Admin Match View"

        match_round = match.round
        opponent = discord_user1 if discord_user1.id != requester_discord_id else discord_user2

        desc_lines = []
        if match_round is not None:
            desc_lines.append(f"**Round:** {match_round}")

        if not admin:
            desc_lines.append(f"**Opponent:** {opponent.mention}")
        else:
            desc_lines.append(
                f"{discord_user1.mention} VS {discord_user2.mention}")

        # Build description text
        description = "\n".join(desc_lines)

        if getattr(tournament, "url", None):
            description += f"\n\n**Bracket:** [View on Challonge]({tournament.url})"

        dt = match.scheduled_datetime
        if dt and opponent:
            ts = int(dt.timestamp())  # unix epoch
            # :F = full date/time, :R = relative (e.g., "in 2 hours")
            description += f"\n\n**Scheduled:** <t:{ts}:F> • <t:{ts}:R>"
        else:
            description += "\n\n💡 Use `/schedule_match` to post your match time in the scheduling channel."

        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color.blurple()
        )
        embed.timestamp = discord.utils.utcnow()
        return embed

    async def _crew_to_discord_member(self, session, interaction: discord.Interaction, participants: list[TournamentParticipants]) -> list[discord.Member]:
        if not interaction.guild:
            return []

        discord_user_list = []
        for participant in participants:
            crew_member = self.__user_id_to_member(
                session, participant.user_id)

            if not crew_member:
                return []

            discord_user = interaction.guild.get_member(
                crew_member.discord_id)

            if not discord_user:
                return []

            discord_user_list.append(discord_user)

        return discord_user_list

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
                return

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

        chall_player1_id = next_match["player1_id"]
        chall_player2_id = next_match["player2_id"]

        participant1 = self.__p_challonge_id_to_participant(
            session, tournament.id, chall_player1_id)
        participant2 = self.__p_challonge_id_to_participant(
            session, tournament.id, chall_player2_id)

        next_match_challonge_id = next_match["id"]
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

    @app_commands.command(name="get_max_round", description="Fetch the max round number of the current Tournament")
    @app_commands.default_permissions(administrator=True)
    async def get_max_round(self, interaction: discord.Interaction):
        max_round = self.max_round
        if not self.current_round:
            await interaction.response.send_message(f"There is either no tournament running or the tournament hasn't started {max_round}", ephemeral=True)

        await interaction.response.send_message(f"The max round number is: {max_round}", ephemeral=True)

    @app_commands.command(name="set_max_round", description="Set the max round number of the current Tournament")
    @app_commands.default_permissions(administrator=True)
    async def set_max_round(self, interaction: discord.Interaction, max_round: str):
        if not max_round.isdigit():
            await interaction.response.send_message(f"Please enter a digit. e.g. 69", ephemeral=True)
            return

        self.max_round = int(max_round)
        if not self.current_tournament:
            await interaction.response.send_message(f"There is currently no tournament running", ephemeral=True)

        await interaction.response.send_message(f"The max round number is: {self.current_round}", ephemeral=True)

    @app_commands.command(name="get_current_round", description="Fetch the current round number of the current Tournament")
    @app_commands.default_permissions(administrator=True)
    async def get_current_round(self, interaction: discord.Interaction):
        current_round = self.current_round
        if not self.current_round:
            await interaction.response.send_message(f"There is either no tournament running or the tournament hasn't started {current_round}", ephemeral=True)

        await interaction.response.send_message(f"The current round number is: {current_round}", ephemeral=True)

    @app_commands.command(name="set_current_round", description="Set the current round number of the current Tournament")
    @app_commands.default_permissions(administrator=True)
    async def set_current_round(self, interaction: discord.Interaction, match_round: str):
        if not match_round.isdigit():
            await interaction.response.send_message(f"Please enter a digit. e.g. 69", ephemeral=True)
            return
        self.current_round = int(match_round)
        if not self.current_tournament:
            await interaction.response.send_message(f"There is currently no tournament running", ephemeral=True)

        await interaction.response.send_message(f"The current round number is: {self.current_round}", ephemeral=True)

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
            self.max_round = fetch_max_round()

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
                    pass
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
                session, participant_winner.user_id)
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

    @start_tournament.autocomplete(name="name")
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
                if not isinstance(new_participant_object, Dict):
                    return None, "new_participant_object is not a dict"

                player_challonge_id = int(
                    new_participant_object["id"])

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
    async def report_win(self, interaction: discord.Interaction, winner: discord.Member, video_link: Optional[str]):
        if interaction.channel_id != int(REPORTS_CH):
            await interaction.response.send_message(
                embed=self.build_simple_embed(
                    "🚫 Wrong Channel", f"Use this command in <#{REPORTS_CH}>.", discord.Color.red()),
                ephemeral=True
            )
            return

        if video_link:
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

        if self.current_round is None or self.max_round is None:
            log.info(f"COMMAND: report_win\nERROR: No self.current_round or self.max_round set")
            return
        
        if self.max_round - self.current_round == 1 or self.max_round == self.current_round:
                if not video_link:
                    await interaction.response.send_message(
                    embed=self.build_simple_embed(
                        "❌ Error", "Semi Finals and Finals require Video Proof. Please add a video link", discord.Color.red()),
                    ephemeral=True
                    )
                    return
        
        slug = slugify(self.current_tournament)
        reporter_discord = interaction.user
        reporter_discord_id = reporter_discord.id
        winner_discord_id = winner.id

        await interaction.response.defer(ephemeral=True, thinking=True)

        with Session.begin() as session:
            tournament = self.__check_if_tournament(session, slug)
            if not tournament:
                await interaction.followup.send(
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
                await interaction.followup.send(
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
                await interaction.followup.send(
                    embed=self.build_simple_embed(
                        "❌ Error", "You are not registered for this tournament.", discord.Color.red()),
                    ephemeral=True
                )
                return

            next_match_ch = self.__find_current_match_player(
                slug, participant.challonge_id)
            if not next_match_ch:
                await interaction.followup.send(
                    embed=self.build_simple_embed(
                        "❌ Error", "No match could be found for this user.", discord.Color.red()),
                    ephemeral=True
                )
                return

            challonge_match_id = next_match_ch["id"]

            player1_ch_id = next_match_ch["player1_id"] if next_match_ch["player1_id"] else None

            player2_ch_id = next_match_ch["player2_id"] if next_match_ch["player2_id"] else None
            round_match = next_match_ch["round"]

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
                await interaction.followup.send(
                    embed=self.build_simple_embed(
                        "❌ Unable to Update", f"{e}", discord.Color.red()),
                    ephemeral=True
                )
                return

            current_match_row = self.__get_match_row_by_chid(
                session, tournament.id, challonge_match_id)
            if not current_match_row:
                await interaction.followup.send(
                    embed=self.build_simple_embed(
                        "❌ Error", "No match could be found.", discord.Color.red()),
                    ephemeral=True
                )
                return

            current_match_row.winner_participant_id = winning_participant.id
            current_match_row.score = score
            current_match_row.completed = True

            if video_link:
                current_match_row.battle_url = video_link

            # Next Match Winner
            await self.__prep_next_match_winner(session, slug, winning_participant.challonge_id)

            # Next Match Loser
            losing_participant = participant1 if participant2 == winning_participant else participant2
            await self.__prep_next_match_winner(session, slug, losing_participant.challonge_id)

            session.flush()

            # Build the single embed
            announce = discord.Embed(
                title=f"🏆 Match Result Reported — Round {round_match}",
                description=f"**{crew_member1.username}** vs **{crew_member2.username}**",
                color=discord.Color.orange()
            )
            announce.add_field(
                name="Winner", value=winner.mention, inline=True)
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

            # Create reward channel
            if not interaction.guild:
                await interaction.followup.send(
                    embed=self.build_simple_embed(
                        "❌ Error", "Discord Server could not be found", discord.Color.red()),
                    ephemeral=True
                )
                return

            is_finished = await self.check_if_finished(session, current_match_row, interaction.guild, winning_crew_member, [crew_member1, crew_member2])
            if is_finished == True:
                try:
                    log_ch = self.bot.get_channel(LOGS_CH) or await self.bot.fetch_channel(LOGS_CH)
                    if log_ch:
                        await log_ch.send(f"All Rounds have been played. Tournament '{self.current_tournament}' can be closed.")
                except Exception:
                    pass
            
            await interaction.followup.send(embed=announce, ephemeral=True)

    @app_commands.command(name="update_match", description="Update the score of a match")
    @app_commands.default_permissions(administrator=True)
    async def update_match(self, interaction: discord.Interaction, player1: discord.Member, player2: discord.Member, winner: discord.Member):
        slug = slugify(self.current_tournament)

        if not self.__winner_reported(player1.id, player2.id, winner.id):
            await interaction.response.send_message(
                embed=self.build_simple_embed(
                    "❌ Error", "Winner must be one of the two players.", discord.Color.red()),
                ephemeral=True
            )
            return
        
        await interaction.response.defer(ephemeral=True, thinking=True)

        with Session.begin() as session:
            tournament = self.__check_if_tournament(session, slug)
            if not tournament:
                await interaction.followup.send(
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
                await interaction.followup.send(
                    embed=self.build_simple_embed(
                        "❌ Error", "1 or more discord users are not crew members", discord.Color.red()),
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
                await interaction.followup.send(
                    embed=self.build_simple_embed(
                        "❌ Error", "One or more crew members are not participants of this tournament.", discord.Color.red()),
                    ephemeral=True
                )
                return

            current_match = self.__get_match_row_for_players(
                session, tournament.id, participant1.id, participant2.id)
            if not current_match:
                await interaction.followup.send(
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

                # Winner's next match
                ok = await self.__prep_next_match_winner(session, slug, winning_participant.challonge_id)

                # Loser's next match
                losing_participant = participant1 if participant2 == winning_participant else participant2
                await self.__prep_next_match_winner(session, slug, losing_participant.challonge_id)

            except challonge.api.ChallongeException as e:
                await interaction.followup.send(
                    embed=self.build_simple_embed(
                        "❌ Update Failed", f"{e}", discord.Color.red()),
                    ephemeral=True
                )
                return

            if not interaction.guild:
                log.info(f"COMMAND: update_match\nERROR: interaction.guild is None")
                return
            
            log.info(f"COMMAND: update_match\nDEBUG: crew member1: {crew_member1.discord_id}\ncrew member2: {crew_member2.discord_id}")
            is_finished = await self.check_if_finished(session, current_match, interaction.guild, winning_crew_member, [crew_member1, crew_member2])
            if is_finished == True:
                try:
                    log_ch = self.bot.get_channel(LOGS_CH) or await self.bot.fetch_channel(LOGS_CH)
                    if log_ch:
                        await log_ch.send(f"All Rounds have been played. Tournament '{self.current_tournament}' can be closed.")
                except Exception:
                    pass
            
            msg = f"Match successfully updated. Winner: **{winner.display_name}**."
            if not ok:
                msg += "\n\n⚠️ Could not find and update winner’s next match."

            await interaction.followup.send(
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
                    if not isinstance(match, Dict):
                        return

                    p1_challonge_id = match["player1_id"]
                    p2_challonge_id = match["player2_id"]
                    winner_challonge_id = match["winner_id"]
                    score_challonge_match = match["scores_csv"]

                    participant1 = self.__p_challonge_id_to_participant(
                        session, tournament.id, p1_challonge_id)
                    participant2 = self.__p_challonge_id_to_participant(
                        session, tournament.id, p2_challonge_id)
                    winning_participant = self.__p_challonge_id_to_participant(
                        session, tournament.id, winner_challonge_id
                    )

                    match_row = self.__get_match_row_by_chid(
                        session, tournament.id, match["id"])
                    match_row.participant1_id = participant1.id if participant1 else None
                    match_row.participant2_id = participant2.id if participant2 else None
                    match_row.winner_participant_id = winning_participant.id if winning_participant else None
                    match_row.score = score_challonge_match if score_challonge_match else None

                    match_row.completed = True if match["state"] == "complete" else False
                    self.current_round = fetch_current_round()

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

    @app_commands.command(name="admin_schedule_match")
    @app_commands.default_permissions(administrator=True)
    async def admin_schedule_match(
            self,
            interaction: discord.Interaction,
            player1: discord.Member,
            player2: discord.Member,
            round_match: app_commands.Range[int, 1, 10],
            year: int,
            month: app_commands.Range[int, 1, 12],
            day: app_commands.Range[int, 1, 31],
            hour: app_commands.Range[int, 0, 23],
            minute: app_commands.Range[int, 0, 59]):

        # CODE START
        slug = slugify(self.current_tournament)
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

        with Session.begin() as session:
            requester_discord = discord_id_to_member(
                session, interaction.user.id)
            if not requester_discord:
                return

            row = self.__get_match_for_users(
                session, slug, round_match, player1.id, player2.id)
            if not row:
                await interaction.followup.send(
                    embed=self.build_simple_embed(
                        "❌ Error", f"Couldn’t find any match between you and your opponent for this round", discord.Color.red()),
                    ephemeral=True
                )
                return

            tournament_url, participant1, participant2, match_row = row

            tz = self.__get_timezone_info(requester_discord)
            if not tz:
                await interaction.followup.send(
                    embed=self.build_simple_embed(
                        "❌ Error", f"No Country or Timezone set. Please use `/set_timezone`, or contact management to set your country.", discord.Color.red()),
                    ephemeral=True
                )
                return

            dt = datetime(
                year=year,
                month=month,
                day=day,
                hour=hour,
                minute=minute,
                tzinfo=tz)

            dt_utc = dt.astimezone(timezone.utc)
            match_row.scheduled_time = dt_utc

            crew_member1 = self.__user_id_to_member(
                session, participant1.user_id)
            crew_member2 = self.__user_id_to_member(
                session, participant2.user_id)
            if not crew_member1 or not crew_member2:
                await interaction.followup.send(
                    embed=self.build_simple_embed(
                        "❌ Error", f"NOT CREW_MEMBER1 {crew_member1}\nNOT CREW_MEMBER2: {crew_member2}\n\n{player1}\n{player2}", discord.Color.red()),
                    ephemeral=True
                )
                return

            discord_user1 = interaction.guild.get_member(
                crew_member1.discord_id)
            discord_user2 = interaction.guild.get_member(
                crew_member2.discord_id)
            if not discord_user1 or not discord_user2:
                await interaction.followup.send(
                    embed=self.build_simple_embed(
                        "❌ Error", f"NOT DISCORD_USER1: {discord_user1}\nNOT DISCORD_USER2: {discord_user2}", discord.Color.red()),
                    ephemeral=True
                )
                return

            new_post_id = await self._post_schedule_embed(dt_utc, discord_user1, discord_user2, round_match, schedule_channel, tournament_url)
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
            match_round: app_commands.Range[int, 1, 10],
            year: int,
            month: app_commands.Range[int, 1, 12],
            day: app_commands.Range[int, 1, 31],
            hour: app_commands.Range[int, 0, 23],
            minute: app_commands.Range[int, 0, 59]):

        # CODE START
        slug = slugify(self.current_tournament)
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

        await interaction.response.defer(ephemeral=True, thinking=True)

        with Session.begin() as session:

            crew_member = discord_id_to_member(session, interaction.user.id)
            if not crew_member:
                await interaction.followup.send(
                    embed=self.build_simple_embed(
                        "❌ Error", "You are not registered in our database. Please contact management.", discord.Color.red()),
                    ephemeral=True
                )
                return

            row = self.__get_match_for_users(
                session, slug, match_round, interaction.user.id, opponent.id)
            if not row:
                await interaction.followup.send(
                    embed=self.build_simple_embed(
                        "❌ Error", f"Couldn’t find any match between you and your opponent for this round", discord.Color.red()),
                    ephemeral=True
                )
                return

            tournament_url, player1, player2, match_row = row

            tz = self.__get_timezone_info(crew_member)
            if not tz:
                await interaction.followup.send(
                    embed=self.build_simple_embed(
                        "❌ Error", f"No Country or Timezone set. Please use `/set_timezone`, or contact management to set your country.", discord.Color.red()),
                    ephemeral=True
                )
                return

            dt = datetime(
                year=year,
                month=month,
                day=day,
                hour=hour,
                minute=minute,
                tzinfo=tz)

            dt_utc = dt.astimezone(timezone.utc)

            participants = [player1, player2]
            discord_user_list = await self._crew_to_discord_member(session, interaction, participants)
            if not discord_user_list and not len(discord_user_list) == 2:
                await interaction.followup.send(
                    embed=self.build_simple_embed(
                        "❌ Error", "1 or more players is not a discord member of the server", discord.Color.red()),
                    ephemeral=True
                )
                return

            discord_user1 = discord_user_list[0]
            discord_user2 = discord_user_list[1]

            match_row.scheduled_datetime = dt_utc

            new_post_id = await self._post_schedule_embed(dt_utc, discord_user1, discord_user2, match_round, schedule_channel, tournament_url)

            if not new_post_id:
                await interaction.followup.send(
                    embed=self.build_simple_embed(
                        "❌ Error", "You cannot schedule a match in the past.", discord.Color.red()),
                    ephemeral=True
                )
                return

            post_url = f"https://discord.com/channels/{interaction.guild.id}/{schedule_channel.id}/{new_post_id}"

            await self._log_to_logs(
                title="🕒 Scheduling Match",
                description=f"By: {interaction.user.mention} ({interaction.user.id})",
                fields={
                    "Round": match_row.round,
                    "Players": f"{discord_user1.mention} vs {discord_user2.mention}",
                    "Bracket": tournament_url,
                    "Channel": f"<#{interaction.channel_id}>",
                    f"Scheduled Time": f"<t:{int(match_row.scheduled_datetime.timestamp())}:F>",
                },
            )

            await interaction.followup.send(
                embed=self.build_simple_embed("✅ Match scheduled!", f"[View post here]({post_url})", discord.Color.green()), ephemeral=True
            )

    @app_commands.command(name="find_current_match", description="Find the details of your current tournament match")
    async def find_current_match(self, interaction: discord.Interaction):
        if interaction.guild_id != int(GUILD_ID):
            await interaction.response.send_message("You cannot use this command from this server/chat")
            return

        slug = slugify(self.current_tournament)
        if not slug:
            await interaction.response.send_message(
                embed=self.build_simple_embed(
                    "ℹ️ Info", "No tournament running right now.", discord.Color.blurple()),
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True, thinking=True)

        with Session() as session:

            row = self.__get_tournament_player(
                session, slug, interaction.user.id)
            if not row:
                await interaction.followup.send(f"❌ You are not registered in the current tournament, or it doesn’t exist.", ephemeral=True)
                return

            tournament, tournament_participant = row

            challonge_match = self.__find_next_match_player(
                slug, tournament_participant.challonge_id)
            if not challonge_match or not challonge_match["id"]:
                # No match for player
                await interaction.followup.send(
                    embed=self.build_simple_embed(
                        "ℹ️ Info", f"No match found on challonge for {interaction.user.display_name}", discord.Color.red()),
                    ephemeral=True
                )
                return

            match_row = self.__get_match_tuple(session, challonge_match["id"])
            if not match_row:
                await interaction.followup.send("❌ No match found in the database for your next Challonge match.", ephemeral=True)
                return

            match, player1, player2 = match_row
            embed = await self.__build_match_embed(
                tournament, match, player1, player2, interaction.user.id, interaction, session)

            if not embed:
                await interaction.followup.send("❌ Could not create embed", ephemeral=True)
                return

            await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="admin_find_match", description="Find the details of any match in the current Tournament")
    @app_commands.default_permissions(administrator=True)
    async def admin_find_match(self, interaction: discord.Interaction, round_number: int, member: discord.Member):
        if interaction.guild_id != int(GUILD_ID):
            await interaction.response.send_message("You cannot use this command from this server/chat")
            return

        slug = slugify(self.current_tournament)
        if not slug:
            await interaction.response.send_message(
                embed=self.build_simple_embed(
                    "ℹ️ Info", "No tournament running right now.", discord.Color.blurple()),
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True, thinking=True)

        with Session.begin() as session:

            player_row = self.__get_tournament_player(
                session, slug, member.id)
            if not player_row:
                await interaction.followup.send(f"❌ You are not registered in the current tournament, or it doesn’t exist.", ephemeral=True)
                return

            tournament, tournament_participant = player_row
            match_row = self.__get_match_participants(
                session, tournament.id, tournament_participant.id, round_number)

            match, player1, player2 = match_row
            embed = await self.__build_match_embed(
                tournament, match, player1, player2, member.id, interaction, session, admin=True)

            if not embed:
                await interaction.followup.send("❌ Could not create embed", ephemeral=True)
                return

            await interaction.followup.send(embed=embed, ephemeral=True)
    
    @app_commands.command(name="finalize_tournament", description="Confirm that all the matches have been played with correct winner details")
    @app_commands.default_permissions(administrator=True)
    async def finalize_tournament(self, interaction: discord.Interaction):
        guild = interaction.guild
        if not guild:
            return

        await interaction.response.defer(ephemeral=True, thinking=True)        
        
        with Session.begin() as session:

            tournament = self.__check_if_tournament(session, self.current_tournament)
        
            # get bronze bronze
            bronze_match = self.__get_final_match(session, tournament.id, tournament_round=0)

            # get final match
            final_match = self.__get_final_match(session, tournament.id, tournament_round=self.max_round)

            if not bronze_match or not final_match:
                await interaction.followup.send(f"Either no Bronze Match or No Final Match completed", ephemeral=True)
                return
            
            bronze_winner = participant_id_to_member(session, tournament.id, bronze_match.winner_participant_id)
            bronze_loser_id = bronze_match.participant1_id if bronze_match.participant2_id == bronze_match.winner_participant_id else bronze_match.participant2_id
            bronze_loser = participant_id_to_member(session, tournament.id, bronze_loser_id)
            
            finals_winner = participant_id_to_member(session, tournament.id, final_match.winner_participant_id)
            finals_loser_id = final_match.participant1_id if final_match.participant2_id == final_match.winner_participant_id else final_match.participant2_id
            finals_loser = participant_id_to_member(session, tournament.id, finals_loser_id)

            if not finals_winner or not finals_loser or not bronze_winner or not bronze_loser:
                await interaction.followup.send(f"Not all matches have been played", ephemeral=True)
                return

            user1 = guild.get_member(finals_winner.discord_id)
            user2 = guild.get_member(finals_loser.discord_id)
            user3 = guild.get_member(bronze_winner.discord_id)
            user4 = guild.get_member(bronze_loser.discord_id)

            if not user1 or not user2 or not user3 or not user4:
                log.info(f"FUNCTION: finalize_tournament\nError: No discord Member for all members.")
                return
            
            announcement_channel = guild.get_channel(ANNOUNCEMENT_CH)
            if isinstance(announcement_channel, discord.TextChannel):
                msg = create_winner_message(self.current_tournament or "", user1, user2, user3, user4, vod_url=final_match.battle_url)
                await announcement_channel.send(msg)

        await interaction.followup.send(f"Finalized Tournament Announcement has been sent", ephemeral=True)

    @app_commands.command(name="edit_vod_link", description="Edit the VOD link of a tournament match")
    @app_commands.default_permissions(administrator=True)
    async def edit_vod_link(self, interaction: discord.Interaction, discord_user1: discord.Member, discord_user2: discord.Member, vod_link: str):
        if vod_link:
            if not validators.url(vod_link):
                await interaction.response.send_message(
                    embed=self.build_simple_embed(
                        "❌ Invalid Link",
                        "Please provide a valid http/https video URL.\n"
                        "Examples:\n• https://youtu.be/xxxx\n• https://streamable.com/xxxx\n• https://limewire.com/xxxx",
                        discord.Color.red()
                    ),
                    ephemeral=True
                )
        else:
            return
        
        await interaction.response.defer(ephemeral=True, thinking=True)
        
        with Session.begin() as session:
            tournament = self.__check_if_tournament(session, self.current_tournament)

            current_match = await self.get_match_for_discord_ids(session, tournament.id, discord_user1.id, discord_user2.id)
            if not current_match:
                await interaction.followup.send(
                    embed=self.build_simple_embed(
                        "❌ Error", f"This match between **{discord_user1.display_name}** and **{discord_user2.display_name}** does not exist.", discord.Color.red()),
                    ephemeral=True
                )
                return

            # Edit Vod Link
            current_match.battle_url = vod_link
            await interaction.followup.send(f"VOD URL successfully updated for this match\nMatch ID {current_match.id}")
    
    @app_commands.command(name="get_match_details", description="Get the details of a match in the current tournament")
    @app_commands.default_permissions(administrator=True)
    async def get_match_details(self, interaction: discord.Interaction, discord_user1: discord.Member, discord_user2: discord.Member):
        await interaction.response.defer(ephemeral=True, thinking=True)

        with Session() as session:
            tournament = self.__check_if_tournament(session, self.current_tournament)

            current_match = await self.get_match_for_discord_ids(session, tournament.id, discord_user1.id, discord_user2.id)
            if not current_match:
                await interaction.followup.send(
                    embed=self.build_simple_embed(
                        "❌ Error", f"This match between **{discord_user1.display_name}** and **{discord_user2.display_name}** does not exist.", discord.Color.red()),
                    ephemeral=True
                )
                return

        # Embed
        embed = discord.Embed(
            title=f"🧩 Match Details — Round {current_match.round}",
            color=discord.Color.blurple()
        )

        embed.add_field(
            name="Participants",
            value=f"**P1 ID:** `{current_match.participant1_id}`\n**P2 ID:** `{current_match.participant2_id}`",
            inline=False
        )

        if current_match.winner_participant_id:
            embed.add_field(
                name="Winner ID",
                value=f"`{current_match.winner_participant_id}`",
                inline=False
            )

        if current_match.battle_url:
            embed.add_field(
                name="VOD Link",
                value=f"<{current_match.battle_url}>",
                inline=False
            )

        if current_match.scheduled_datetime:
            ts = int(current_match.scheduled_datetime.timestamp())
            embed.add_field(
                name="Scheduled",
                value=f"<t:{ts}:F>\n<t:{ts}:R>",
                inline=False
            )

        embed.set_footer(text=f"Tournament ID: {current_match.tournament_id}")
        embed.timestamp = discord.utils.utcnow()
        
        await interaction.followup.send(embed=embed, ephemeral=True)
            
    
    async def helper(self, session, guild: discord.Guild, tournament, discord_user1: discord.Member, discord_user2: discord.Member, winner: discord.Member):
        slug = tournament.slug
        status = "✅"

        crew_member1 = discord_id_to_member(session, discord_user1.id)
        crew_member2 = discord_id_to_member(session, discord_user2.id)
        winning_crew_member = discord_id_to_member(
            session, winner.id)
        
        if not crew_member1 or not crew_member2 or not winning_crew_member:
            return "❌ Error", f"1 or more discord users are not crew members"

        participant1 = self.__check_if_participant(
            session, tournament.id, crew_member1.id)
        participant2 = self.__check_if_participant(
            session, tournament.id, crew_member2.id)
        winning_participant = self.__check_if_participant(
            session, tournament.id, winning_crew_member.id)


        if not participant1 or not participant2:
            return "❌ Error", "One or more crew members are not participants of this tournament."

        current_match = self.__get_match_row_for_players(
            session, tournament.id, participant1.id, participant2.id)
        if not current_match:
            return "❌ Error", f"This match between **{discord_user1.display_name}** and **{discord_user2.display_name}** does not exist."

        score = "1-0" if winning_participant.id == current_match.participant1_id else "0-1"
        
        try:
            challonge.matches.update(
                slug, current_match.challonge_id, scores_csv=score, winner_id=winning_participant.challonge_id)
            current_match.completed = True
            current_match.score = score
            current_match.winner_participant_id = winning_participant.id

            # Winner's next match
            ok = await self.__prep_next_match_winner(session, slug, winning_participant.challonge_id)

            # Loser's next match
            losing_participant = participant1 if participant2 == winning_participant else participant2
            await self.__prep_next_match_winner(session, slug, losing_participant.challonge_id)

        except challonge.api.ChallongeException as e:
            return "❌ Update Failed", f"{e}"

        if not guild:
            log.info(f"COMMAND: update_match\nERROR: interaction.guild is None")
            return
        
        log.info(f"COMMAND: update_match\nDEBUG: crew member1: {crew_member1.discord_id}\ncrew member2: {crew_member2.discord_id}")
        is_finished = await self.check_if_finished(session, current_match, guild, winning_crew_member, [crew_member1, crew_member2])
        if is_finished == True:
            try:
                log_ch = self.bot.get_channel(LOGS_CH) or await self.bot.fetch_channel(LOGS_CH)
                if log_ch:
                    await log_ch.send(f"All Rounds have been played. Tournament '{self.current_tournament}' can be closed.")
            except Exception:
                pass
        
        msg = f"Match successfully updated. Winner: **{winner.mention}**."
        if not ok:
            msg += "\n\n⚠️ Could not find and update winner’s next match."

        return status, msg
    
    @app_commands.command(name="random_match_winner", description="Randomly choose a winner of a match in the current tournament")
    @app_commands.default_permissions(administrator=True)
    async def random_match_winner(self, interaction: discord.Interaction, discord_user1: discord.Member, discord_user2: discord.Member):
        guild = interaction.guild
        if not guild:
            await interaction.response.send_message(
                embed=self.build_simple_embed(
                    "❌ Error", "Command can only be used in the server", discord.Color.red()),
                ephemeral=True
            )
            return
        
        slug = slugify(self.current_tournament)

        winner = choice([discord_user1, discord_user2])

        if not self.__winner_reported(discord_user1.id, discord_user2.id, winner.id):
            await interaction.response.send_message(
                embed=self.build_simple_embed(
                    "❌ Error", "Winner must be one of the two players.", discord.Color.red()),
                ephemeral=True
            )
            return
        
        await interaction.response.defer(ephemeral=False, thinking=True)

        with Session.begin() as session:
            tournament = self.__check_if_tournament(session, slug)
            if not tournament:
                await interaction.followup.send(
                    embed=self.build_simple_embed(
                        "ℹ️ Info", "There is currently no tournament set as current tournament.", discord.Color.blurple()),
                    ephemeral=True
                )
                return

            embed_color = discord.Color.green()
            status, msg = await self.helper(session, guild, tournament, discord_user1, discord_user2, winner)
            
            if "❌" in status:
                embed_color = discord.Color.red()

            await interaction.followup.send(
                embed=self.build_simple_embed(
                    "✅ Match Updated", msg, embed_color), ephemeral=False
            )

    @app_commands.command(name="create_reward_channels", description="Create channels for unreceived rewards")
    @app_commands.default_permissions(administrator=True)
    async def create_reward_channels(self, interaction: discord.Interaction):
        guild = interaction.guild
        slug = slugify(self.current_tournament)

        if not guild:
            return
        
        with Session() as session:
            tournament =  self.__check_if_tournament(session, slug)
            if not tournament:
                await interaction.response.send_message(f"There is currently no tournament going on.")

            await interaction.response.defer(ephemeral=True, thinking=True)
            
            stmt = (
                select(User)
                .join(TournamentParticipants, TournamentParticipants.user_id == User.id)
                .where(
                    TournamentParticipants.tournament_id == tournament.id,
                    TournamentParticipants.reward_received == False
                )
            )
            crew_members = list(session.scalars(stmt).all()) 
            if len(crew_members) == 0:
                await interaction.followup.send(f"There are no participants that still need to receive a reward")

            channel_amount = await self.channel_factory.tournament_rewards(guild, crew_members, REWARDS_CATEGORY, slug)
            await interaction.followup.send(f"{channel_amount} reward channels have been created", ephemeral=True)


    @app_commands.command(name="reward_participant", description="Confirm that a player has received a reward in the current tournament")
    @app_commands.default_permissions(administrator=True)
    async def reward_player(self, interaction: discord.Interaction, member: discord.Member):
        slug = slugify(self.current_tournament)
        if not slug:
            await interaction.response.send_message(f"There is currently no tournament going on.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True, thinking=True)

        with Session.begin() as session:
            crew_member = discord_id_to_member(session, member.id)
            tournament = self.__check_if_tournament(session, slug)

            if not crew_member:
                await interaction.followup.send(f"Crew Member is not registered in our database.", ephemeral=True)
                return

            participant = self.__check_if_participant(session, tournament.id, crew_member.id)
            if not participant:
                await interaction.followup.send(f"{crew_member.username} is not a participant for this tournament.", ephemeral=True)
                return

            participant.reward_received = True
            participant.reward_received_on = datetime.now(timezone.utc)

            await interaction.followup.send(f"Rewards Successfully rewarded", ephemeral=True)

    @app_commands.command(name="participant_info", description="Get the details of a participant in the current tournament")
    async def participant_info(self, interaction: discord.Interaction, member: discord.Member):
        slug = slugify(self.current_tournament)
        if not slug:
            await interaction.response.send_message("There is currently no tournament set.", ephemeral=True)
            return

        with Session() as session:
            crew_member = discord_id_to_member(session, member.id)
            tournament = self.__check_if_tournament(session, slug)

            if not crew_member:
                await interaction.response.send_message("❌ Crew member is not registered in our database.", ephemeral=True)
                return

            if not tournament:
                await interaction.response.send_message("❌ Current tournament not found in the database.", ephemeral=True)
                return

            participant = self.__check_if_participant(session, tournament.id, crew_member.id)
            if not participant:
                await interaction.response.send_message(
                    f"❌ **{crew_member.username}** is not a participant for **{tournament.name}**.",
                    ephemeral=True
                )
                return

            p_id = participant.id
            challonge_pid = participant.challonge_id

            m_p1 = participant.matches_row_p1 or []
            m_p2 = participant.matches_row_p2 or []
            all_matches = list(m_p1) + list(m_p2)

            played = len(all_matches)
            completed = sum(1 for m in all_matches if m.completed)
            wins = sum(1 for m in all_matches if m.winner_participant_id == p_id)

            # Next (incomplete) match for this participant (pick the first)
            next_match = next(
                (m for m in all_matches if not m.completed),
                None
            )
            next_sched = getattr(next_match, "scheduled_datetime", None)

            # Reward status
            rewarded = bool(participant.reward_received)
            rewarded_on = participant.reward_received_on
            rewarded_str = "✅ Received" if rewarded else "❌ Not received"
            rewarded_time_str = (
                f"<t:{int(rewarded_on.timestamp())}:F>" if rewarded and rewarded_on else "—"
            )

            # --- Embed ---
            embed = discord.Embed(
                title=f"🧾 Participant Info — {tournament.name}",
                color=discord.Color.blurple()
            )
            embed.set_author(name=member.display_name, icon_url=getattr(member.display_avatar, "url", None))
            embed.set_thumbnail(url=getattr(member.display_avatar, "url", None))

            # Identity / IDs
            embed.add_field(name="Trainer", value=member.mention, inline=True)
            embed.add_field(name="IGN", value=crew_member.username or "—", inline=True)
            embed.add_field(name="Participant ID", value=str(p_id), inline=True)

            # Challonge linkage
            embed.add_field(name="Challonge Participant", value=str(challonge_pid or "—"), inline=True)
            embed.add_field(name="Tournament Round(s)", value=(", ".join({str(m.round) for m in all_matches}) or "—"), inline=True)
            embed.add_field(name="Tournament Link", value=f"[Open]({tournament.url})", inline=True)

            # Match stats
            embed.add_field(name="Matches Played", value=str(played), inline=True)
            embed.add_field(name="Completed", value=str(completed), inline=True)
            embed.add_field(name="Wins", value=str(wins), inline=True)

            # Next match (if any / scheduled)
            if next_sched:
                ts = int(next_sched.timestamp())
                embed.add_field(name="Next Match", value=f"<t:{ts}:F>\n<t:{ts}:R>", inline=False)
            elif played != completed:
                embed.add_field(name="Next Match", value="Pending (not scheduled)", inline=False)

            # Reward status
            embed.add_field(name="Reward Status", value=f"{rewarded_str}\n{rewarded_time_str}", inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Tournaments(bot))
