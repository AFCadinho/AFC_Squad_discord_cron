import discord
import os
from discord import app_commands
from discord.ext import commands
from database.models import Session, Pokemon, User


CATEGORY_ID = int(os.environ.get("LENDING_CATEGORY", "123456789012345678"))  # Category for lending channels
STAFF_ROLE_ID = int(os.environ.get("STAFF_ROLE", "123456789012345678"))  # Role for staff members


class CreateChannelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180) 

    @discord.ui.button(label="Create Channel", style=discord.ButtonStyle.primary)
    async def create_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        if guild is None:
            return await interaction.response.send_message("This only works in a server.", ephemeral=True)

        category = guild.get_channel(CATEGORY_ID)
        if not isinstance(category, discord.CategoryChannel):
            return await interaction.response.send_message("⚠ Category not found.", ephemeral=True)

        # Private to requester + staff
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user:   discord.PermissionOverwrite(view_channel=True, send_messages=True),
        }
        staff_role = guild.get_role(STAFF_ROLE_ID)
        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        # Simple, safe-ish name
        name = f"lending-{interaction.user.name}".lower().replace(" ", "-")

        new_channel = await guild.create_text_channel(
            name=name,
            category=category,
            overwrites=overwrites,
            topic=f"user:{interaction.user.id}"
        )

        await interaction.response.send_message(f"✅ Created {new_channel.mention}", ephemeral=True)
        await new_channel.send(f"{interaction.user.mention} Welcome! A staff member will assist you shortly.")


class Lending(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def autocomplete_pokemon_name(self, interaction: discord.Interaction, current: str):
        session = Session()
        with session:
            results = (
                session.query(Pokemon)
                .filter(Pokemon.name.ilike(f"%{current}%"))
                .limit(25)
                .all()
            )
        return [
            app_commands.Choice(name=p.name, value=p.name)
            for p in results
        ]
    
    @app_commands.command(name="lending_info", description="Post a public lending info embed (no buttons).")
    @app_commands.default_permissions(administrator=True)
    async def lending_info(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Pokémon Lending — How it Works",
            description=(
                "Borrow competitive-ready Pokémon from our pool.\n"
                "Follow the steps below to check availability and start your request."
            ),
            color=discord.Color.blurple()
        )
        embed.add_field(
            name="1) Check availability",
            value="Use **`/search_pokemon name:<pokemon>`** to see if it exists and is available.",
            inline=False
        )
        embed.add_field(
            name="2) Request lending",
            value=(
                "Use **`/request_lending name:<pokemon>`**.\n"
                "• If the Pokémon is available, the bot will send **you** a private (ephemeral) embed with a **Create Channel** button.\n"
                "• Click it to open a private channel with staff to arrange the lend."
            ),
            inline=False
        )
        embed.add_field(
            name="Notes",
            value=(
                "• One active lending channel per user.\n"
                "• Keep all lending discussions in your private channel with staff.\n"
                "• Misuse may result in loss of lending privileges."
            ),
            inline=False
        )
        # Optional: add a footer or thumbnail
        embed.set_footer(text="AFC Squad • Lending Program")

        await interaction.response.send_message(embed=embed)  # public


    @app_commands.command(name="request_lending", description="Send you a private embed with a button to create a channel.")
    async def request_lending(self, interaction: discord.Interaction, name: str):
        
        session = Session()
        with session:
            is_available = (session.query(Pokemon)
                            .filter(Pokemon.name.ilike(name))
                            .filter(Pokemon.loaned == False)
                            .first() is not None)
            
            if not is_available:
                return await interaction.response.send_message(
                    f"⚠ Pokémon `{name}` is not available for lending.",
                    ephemeral=True
                )
        
        embed = discord.Embed(
            title="Request Lending",
            description="Click the button below to create your private lending channel.",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, view=CreateChannelView(), ephemeral=True)

    @request_lending.autocomplete("name")
    async def autocomplete_name(self, interaction: discord.Interaction, current: str):
        return await self.autocomplete_pokemon_name(interaction, current)


    @app_commands.command(name="lend_approve", description="Approve a lending request (staff only).")
    @app_commands.default_permissions(manage_channels=True)
    async def lend_approve(self, interaction: discord.Interaction, member: discord.Member , pokemon_name: str):
        session = Session()

        with session:
            requesting_user = session.query(User).filter_by(discord_id=member.id)
            if not requesting_user:
                await interaction.response.send_message(f"User with discord id: {member.id} does not exist")


async def setup(bot: commands.Bot):
    await bot.add_cog(Lending(bot))
