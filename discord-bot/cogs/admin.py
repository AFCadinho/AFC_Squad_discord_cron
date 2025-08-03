import discord
from discord.ext import commands
from discord import app_commands
from database.models import Session, User


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="register_user", description="Register a user in the database")
    @app_commands.default_permissions(administrator=True)
    async def register_user(self, interaction: discord.Interaction, user: discord.User, ign: str, country: str):
        session = Session()

        with session:
            existing_user = session.query(User).filter_by(discord_id=user.id).first()
            if existing_user:
                await interaction.response.send_message(f"User with Discord ID {user.id} already exists.", ephemeral=True)
                return
            
            new_user = User(
                discord_id=user.id,
                username=ign,
                country_timezone=country
            )
            session.add(new_user)
            session.commit()
            await interaction.response.send_message(f"User {ign} with Discord ID {user.id} registered successfully.", ephemeral=True)


    @app_commands.command(name="remove_user", description="Remove a user from the database")
    @app_commands.default_permissions(administrator=True)
    async def remove_user(self, interaction: discord.Interaction, user: discord.User):
        session = Session()

        with session:
            existing_user = session.query(User).filter_by(discord_id=user.id).first()
            if not existing_user:
                await interaction.response.send_message(f"User with Discord ID {user.id} does not exist.", ephemeral=True)
                return
            
            session.delete(existing_user)
            session.commit()
            await interaction.response.send_message(f"User {existing_user.username} with Discord ID {user.id} removed successfully.", ephemeral=True)

    @app_commands.command(name="toggle_active_status", description="Toggle the active status of a user")
    @app_commands.default_permissions(administrator=True)
    async def toggle_active_status(self, interaction: discord.Interaction, user: discord.User):
        session = Session()

        with session:
            existing_user = session.query(User).filter_by(discord_id=user.id).first()
            if not existing_user:
                await interaction.response.send_message(f"User with Discord ID {user.id} does not exist.", ephemeral=True)
                return
            
            existing_user.is_active = not existing_user.is_active
            session.commit()
            status = "active" if existing_user.is_active else "inactive"
            await interaction.response.send_message(f"User {existing_user.username} with Discord ID {user.id} is now {status}.", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Admin(bot))
