import os
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

# Role IDs from .env
CWS_PING_ROLE = int(os.getenv("CWS_PING_ROLE", "0"))
PVP_ROLE = int(os.getenv("PVP_ROLE", "0"))
NEW_RECRUIT = int(os.getenv("NEW_RECRUIT_ROLE", "0"))
CREW_MEMBER_ROLE = int(os.getenv("CREW_MEMBER_ROLE", "0"))

class MembershipRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def is_admin(self, member: discord.Member) -> bool:
        return member.guild_permissions.administrator

    async def get_roles(self, guild: discord.Guild, *role_ids: int):
        return [discord.utils.get(guild.roles, id=role_id) for role_id in role_ids]

    @app_commands.command(name="make_new_recruit", description="Welcome someone as a new recruit to the crew")
    @app_commands.describe(member="Select the member to promote to New Recruit")
    async def make_new_recruit(self, interaction: discord.Interaction, member: discord.Member):
        if interaction.guild is None:
            return await interaction.response.send_message("❌ This command can only be used in a server.", ephemeral=True)

        issuer = interaction.guild.get_member(interaction.user.id)
        if issuer is None or not self.is_admin(issuer):
            return await interaction.response.send_message("❌ You need to be a server admin to use this command.", ephemeral=True)

        roles = await self.get_roles(interaction.guild, CWS_PING_ROLE, PVP_ROLE, NEW_RECRUIT)
        await member.add_roles(*[r for r in roles if r])

        await interaction.response.send_message(
            f"🌟 @everyone welcome **{member.mention}**, our newest **New Recruit**!\nLet’s make some memories together 🚀",
            ephemeral=False
        )

    @app_commands.command(name="make_full_member", description="Promote a new recruit to full member status")
    @app_commands.describe(member="Select the member to promote to Full Member")
    async def make_full_member(self, interaction: discord.Interaction, member: discord.Member):
        if interaction.guild is None:
            return await interaction.response.send_message("❌ This command can only be used in a server.", ephemeral=True)

        issuer = interaction.guild.get_member(interaction.user.id)
        if issuer is None or not self.is_admin(issuer):
            return await interaction.response.send_message("❌ You need to be a server admin to use this command.", ephemeral=True)

        try_out_role = discord.utils.get(interaction.guild.roles, id=NEW_RECRUIT)
        full_member_role = discord.utils.get(interaction.guild.roles, id=CREW_MEMBER_ROLE)

        if try_out_role in member.roles:
            if try_out_role:
                await member.remove_roles(try_out_role)

        if full_member_role:
            await member.add_roles(full_member_role)

        await interaction.response.send_message(
            f"🔥 @everyone Let’s gooo!!! **{member.mention}** just got promoted to **FULL CREW MEMBER**! 🎉 Show 'em some love! 💯",
            ephemeral=False
        )

async def setup(bot):
    await bot.add_cog(MembershipRoles(bot))
