import discord
from discord.ext import commands
from discord import app_commands
from database.models import User
from database.database import Session

from sqlalchemy import select    
from datetime import datetime
from helpers import EmbedFactory

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.embed = EmbedFactory(bot)
        self.pvp_experiences = ["novice", "intermediate", "veteran"]

    @staticmethod
    def get_user_by_discord_id(session, discord_id: int) -> User | None:
        stmt = select(User).where(User.discord_id == discord_id)
        return session.scalars(stmt).first()

    @app_commands.command(name="register_user", description="Register a user in the database")
    @app_commands.default_permissions(administrator=True)
    @app_commands.choices(pvp_experience=[
        app_commands.Choice(name="Novice", value="novice"),
        app_commands.Choice(name="Intermediate", value="intermediate"),
        app_commands.Choice(name="Veteran", value="veteran"),
    ])
    async def register_user(self, interaction: discord.Interaction, member: discord.Member, ign: str, country: str, pvp_experience: app_commands.Choice[str]):

        with Session() as session:
            existing_user = self.get_user_by_discord_id(session, member.id)
            if existing_user:
                await interaction.response.send_message(f"User with Discord ID {member.id} already exists.", ephemeral=True)
                return

            new_user = User(
                discord_id=member.id,
                username=ign,
                country=country,
                pvp_experience=pvp_experience.value
            )
            session.add(new_user)
            session.commit()
            await interaction.response.send_message(f"User {ign} with Discord ID {member.id} registered successfully.", ephemeral=True)

    @app_commands.command(name="remove_user", description="Remove a user from the database")
    @app_commands.default_permissions(administrator=True)
    async def remove_user(self, interaction: discord.Interaction, user: discord.User):

        with Session() as session:
            existing_user = self.get_user_by_discord_id(session, user.id)
            if not existing_user:
                await interaction.response.send_message(f"User with Discord ID {user.id} does not exist.", ephemeral=True)
                return

            session.delete(existing_user)
            session.commit()
            await interaction.response.send_message(f"User {existing_user.username} with Discord ID {user.id} removed successfully.", ephemeral=True)

    @app_commands.command(name="edit_user", description="Edit the data of a user")
    @app_commands.default_permissions(administrator=True)
    @app_commands.choices(data_to_edit=[
        app_commands.Choice(name="Username", value="username"),
        app_commands.Choice(name="Country/Timezone", value="country"),
        app_commands.Choice(name="Joined at", value="created_at"),
        app_commands.Choice(name="PvP Experience", value="pvp_experience"),
    ])
    async def edit_user(self, interaction: discord.Interaction, user: discord.User, data_to_edit: app_commands.Choice[str], new_value: str):
        
        with Session.begin() as session:
            existing_user = self.get_user_by_discord_id(session, user.id)
            if not existing_user:
                await interaction.response.send_message(f"User with Discord ID {user.id} does not exist.", ephemeral=True)
                return
            
            match data_to_edit.value:
                case "username":
                    existing_user.username = new_value
                case "country":
                    existing_user.country = new_value
                case "created_at":
                    try:
                        new_date = datetime.strptime(new_value, "%d-%m-%Y")
                        existing_user.created_at = new_date
                    except ValueError:
                        await interaction.response.send_message(
                            "Invalid date format. Please use `DD-MM-YYYY` (e.g. `19-09-2025`).",
                            ephemeral=True
                        )
                        return
                case "pvp_experience":
                    if new_value.lower() not in self.pvp_experiences:
                        await interaction.response.send_message("Not a valid option. Please choose: ['novice', 'intermediate', 'veteran']")
                        return

                    existing_user.pvp_experience = new_value
                case _:
                    await interaction.response.send_message("Invalid option")
            
            await interaction.response.send_message("Userdata successfully edited")
                

    @app_commands.command(name="toggle_active_status", description="Toggle the active status of a user")
    @app_commands.default_permissions(administrator=True)
    async def toggle_active_status(self, interaction: discord.Interaction, user: discord.User):

        with Session() as session:
            existing_user = self.get_user_by_discord_id(session, user.id)
            if not existing_user:
                await interaction.response.send_message(f"User with Discord ID {user.id} does not exist.", ephemeral=True)
                return

            existing_user.is_active = not existing_user.is_active
            session.commit()
            status = "active" if existing_user.is_active else "inactive"
            await interaction.response.send_message(f"User {existing_user.username} with Discord ID {user.id} is now {status}.", ephemeral=True)

    @app_commands.command(name="search_user", description="Search information about a user in the database")
    @app_commands.default_permissions(administrator=True)
    async def search_user(self, interaction: discord.Interaction, user: discord.User):
        # DB lookup
        with Session() as session:
            row = self.get_user_by_discord_id(session, user.id)
            if not row:
                await interaction.response.send_message(
                    f"No record found for Discord ID `{user.id}`.",
                    ephemeral=True
                )
                return

        embed = discord.Embed(
            title="User Details",
            color=discord.Color.blurple()
        )
        embed.set_author(name=user.name, icon_url=getattr(
            user.display_avatar, "url", None))
        embed.set_thumbnail(url=getattr(user.display_avatar, "url", None))

        # Core DB info
        embed.add_field(name="IGN", value=row.username, inline=True)
        embed.add_field(name="Discord ID", value=str(
            row.discord_id), inline=True)
        embed.add_field(name="Active", value=(
            "✅ Yes" if row.is_active else "❌ No"), inline=True)

        embed.add_field(name="PvP Experience",
                        value=row.pvp_experience.title(), inline=True)
        embed.add_field(name="Country / Timezone",
                        value=(row.country or "—"), inline=True)
        embed.add_field(name="Join Date", value=str(
            row.created_at.strftime("%d-%m-%Y")), inline=True)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="say_hello_world")
    async def say_hello_world(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            embed=self.embed.success(f"Hello World"), ephemeral=True
        )

async def setup(bot: commands.Bot):
    await bot.add_cog(Admin(bot))
