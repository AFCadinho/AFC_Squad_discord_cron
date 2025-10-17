import discord
import os

from discord import app_commands
from discord.ext import commands
from helpers import ChannelFactory
from database.models import TournamentMatches, TournamentParticipants, User, Tournament
from sqlalchemy import select
from database.database import Session
from sqlalchemy.orm import aliased

TOURNAMENT_MATCHES_CATEGORY = int(os.getenv("MATCHES_CAT_ID", 0)) 

class Testing(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.channel_factory = ChannelFactory(bot)

    async def get_match_info(self, session, match_round):
        stmt = (
            select(TournamentMatches).
            where(
                TournamentMatches.tournament_id == 3,
                TournamentMatches.round == match_round
            )
        ) 
        return session.scalars(stmt).all()
    
    async def get_participants(self, session, match):

        u1 = aliased(User)
        u2 = aliased(User)
        p1 = aliased(TournamentParticipants)
        p2 = aliased(TournamentParticipants)
        
        stmt = (
            select(u1, u2)
            .select_from(TournamentMatches)
            .join(Tournament, Tournament.id == TournamentMatches.tournament_id)
            .join(p1, p1.id == TournamentMatches.participant1_id)
            .join(p2, p2.id == TournamentMatches.participant2_id)
            .join(u1, u1.id == p1.user_id)
            .join(u2, u2.id == p2.user_id)
            .where(
                TournamentMatches.tournament_id == match.tournament_id,
                TournamentMatches.round == match.round,
                TournamentMatches.id == match.id
            )
        ) 
        return session.execute(stmt).first()
        

    async def delete_channels(self, guild: discord.Guild, category_id):
        discord_category = discord.utils.get(guild.categories, id=category_id)
        if not discord_category:
            return
        for channel in discord_category.channels:
            await channel.delete()

    
    @app_commands.command(name="create_channel", description="create a channel")
    @app_commands.default_permissions(administrator=True)
    async def create_channel(self, interaction: discord.Interaction):
        if not interaction.guild:
            return
        
        await interaction.response.defer(ephemeral=True, thinking=True)
        
        with Session.begin() as session:
            match_round = 1
            
            new_matches = await self.get_match_info(session, match_round)
            if not new_matches:
                return

            await self.delete_channels(interaction.guild, TOURNAMENT_MATCHES_CATEGORY)
            
            for match in new_matches:
                u1, u2 = await self.get_participants(session, match)

                users = [u1, u2]

                channel_name = await self.channel_factory.tournament_match(interaction.guild, users=users, category_id=TOURNAMENT_MATCHES_CATEGORY)
                if not channel_name:
                    return

                await interaction.followup.send(f"Text channel create: {channel_name}")


async def setup(bot):
    await bot.add_cog(Testing(bot))