import discord
import sqlalchemy as sa
from discord import app_commands
from discord.ext import commands
from database.models import Pokemon
from database.database import Session


class CrewPokemon(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.always_sync_count = 9
        self.always_bosses_count = 6

    @app_commands.command(name="register_pokemon", description="Register a Pokémon in the database")
    @app_commands.default_permissions(administrator=True)
    @app_commands.choices(
        tier=[
            app_commands.Choice(name="OU", value="ou"),
            app_commands.Choice(name="UU", value="uu"),
        ]
    )
    async def register_pokemon(self, interaction: discord.Interaction, name: str, ability: str, nature: str, tier: app_commands.Choice[str], discord_link: str):
        session = Session()

        with session:
            existing_pokemon = session.query(
                Pokemon).filter_by(name=name).first()
            if existing_pokemon:
                await interaction.response.send_message(f"Pokémon {name} already exists in the database.", ephemeral=True)
                return

            new_pokemon = Pokemon(
                name=name,
                ability=ability,
                nature=nature,
                tier=tier.value,
                discord_link=discord_link,
            )
            session.add(new_pokemon)
            session.commit()
            await interaction.response.send_message(f"Pokémon {name} registered successfully.", ephemeral=True)

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

    @app_commands.command(name="remove_pokemon", description="Remove a Pokémon from the database")
    @app_commands.default_permissions(administrator=True)
    async def remove_pokemon(self, interaction: discord.Interaction, name: str):
        session = Session()

        with session:
            existing_pokemon = session.query(
                Pokemon).filter_by(name=name).first()
            if not existing_pokemon:
                await interaction.response.send_message(f"Pokémon {name} does not exist in the database.", ephemeral=True)
                return

            session.delete(existing_pokemon)
            session.commit()
            await interaction.response.send_message(f"Pokémon {name} removed successfully.", ephemeral=True)

    @app_commands.command(name="edit_pokemon", description="Edit a Pokémon's details in the database")
    @app_commands.default_permissions(administrator=True)
    @app_commands.choices(
        field=[
            app_commands.Choice(name="Name", value="name"),
            app_commands.Choice(name="Ability", value="ability"),
            app_commands.Choice(name="Nature", value="nature"),
            app_commands.Choice(name="Tier", value="tier"),
            app_commands.Choice(name="Discord Link", value="discord_link"),
            app_commands.Choice(name="Always_stored", value="always_stored"),
        ]
    )
    async def edit_pokemon(self, interaction: discord.Interaction, name: str, field: app_commands.Choice[str], value: str):
        session = Session()
        with session:
            existing_pokemon = session.query(
                Pokemon).filter_by(name=name).first()
            if not existing_pokemon:
                await interaction.response.send_message(f"Pokémon {name} does not exist in the database.", ephemeral=True)
                return

            if field.value.lower() == "always_stored":
                if value.lower() not in ["true", "false"]:
                    await interaction.response.send_message("Invalid value for always_stored. Use 'true' or 'false'.", ephemeral=True)
                    return
                existing_pokemon.always_stored = True if value.lower() == "true" else False
                existing_pokemon.in_storage = True if value.lower() == "true" else False
            else:
                setattr(existing_pokemon, field.value, value)
            session.commit()
            await interaction.response.send_message(f"Pokémon {name} updated successfully: {field.name} set to {value}.", ephemeral=True)

    @remove_pokemon.autocomplete("name")
    async def autocomplete_remove_pokemon(self, interaction: discord.Interaction, current: str):
        return await self.autocomplete_pokemon_name(interaction, current)

    @edit_pokemon.autocomplete("name")
    async def autocomplete_edit_pokemon(self, interaction: discord.Interaction, current: str):
        return await self.autocomplete_pokemon_name(interaction, current)

    @app_commands.command(name="fill_storage", description="Fill the Pokémon storage with random Pokémon")
    @app_commands.default_permissions(administrator=True)
    @app_commands.choices(
        tier=[
            app_commands.Choice(name="OU", value="ou"),
            app_commands.Choice(name="UU", value="uu"),
        ]
    )
    async def fill_storage(self, interaction: discord.Interaction, count: int, tier: app_commands.Choice[str]):
        
        session = Session()
        pvp_in_storage_count = (
                session.query(Pokemon)
                .filter_by(in_storage=True, always_stored=True, tier=tier.value)
                .count()
            )

        if count > (25 - pvp_in_storage_count - self.always_sync_count - self.always_bosses_count):
            await interaction.response.send_message("Count is higher than storage amount.", ephemeral=True)
            return
        
        with session:

            candidate_pokemon = (
                session.query(Pokemon)
                .filter(
                    Pokemon.tier.ilike(tier.value),
                    Pokemon.in_storage == False,
                    Pokemon.loaned == False,
                    Pokemon.always_stored == False,
                )
                .order_by(sa.func.random())
                .limit(count)
                .all()
            )


            if not candidate_pokemon:
                await interaction.response.send_message(f"No Pokémon available in tier {tier.name} for storage.", ephemeral=True)
                return

            for pokemon in candidate_pokemon:
                pokemon.in_storage = True

            await interaction.response.send_message(
                f"Filled storage with {len(candidate_pokemon)} Pokémon of tier {tier.name}.",
                ephemeral=True
            )

            session.commit()

    @app_commands.command(name="clear_storage", description="Clear the Pokémon storage")
    @app_commands.default_permissions(administrator=True)
    async def clear_storage(self, interaction: discord.Interaction):
        session = Session()

        with session:
            stored_pokemon = session.query(Pokemon).filter_by(in_storage=True, always_stored=False).all()
            if not stored_pokemon:
                await interaction.response.send_message("No Pokémon in storage to clear.", ephemeral=True)
                return

            for pokemon in stored_pokemon:
                pokemon.in_storage = False

            session.commit()
            await interaction.response.send_message(f"Cleared {len(stored_pokemon)} Pokémon from storage.", ephemeral=True)


    @app_commands.command(name="list_storage", description="List all Pokémon in storage")
    async def list_storage(self, interaction: discord.Interaction):
        session = Session()

        with session:
            stored_pokemon = session.query(Pokemon).filter_by(in_storage=True).all()
            if not stored_pokemon:
                await interaction.response.send_message("No Pokémon in storage.", ephemeral=True)
                return

            embed = discord.Embed(title="Pokémon in Crew Storage", color=discord.Color.blue())
            for pokemon in stored_pokemon:
                link_text = f"[Link]({pokemon.discord_link})" if pokemon.discord_link else "No Link"
                embed.add_field(
                    name=pokemon.name, 
                    value=link_text, 
                    inline=False)

            await interaction.response.send_message(embed=embed, ephemeral=True)


    @app_commands.command(name="search_pokemon", description="Search for Pokémon by name")
    async def search_pokemon(self, interaction: discord.Interaction, name: str):
        session = Session()

        with session:
            pokemon = session.query(Pokemon).filter_by(name=name).first()
            if not pokemon:
                await interaction.response.send_message(f"No Pokémon found with name {name}.", ephemeral=True)
                return

            embed = discord.Embed(title=f"{pokemon.name}", color=discord.Color.green())
            embed.add_field(name="Ability", value=pokemon.ability, inline=True)
            embed.add_field(name="Nature", value=pokemon.nature, inline=True)
            embed.add_field(name="Tier", value=pokemon.tier or "N/A", inline=True)
            embed.add_field(name="Available", value="Yes" if not pokemon.loaned and not pokemon.in_storage else "No", inline=True)
            link_text = f"[Link]({pokemon.discord_link})" if pokemon.discord_link else "No Link"
            embed.add_field(name="Discord Link", value=link_text, inline=False)

            await interaction.response.send_message(embed=embed, ephemeral=True)


    @search_pokemon.autocomplete("name")
    async def autocomplete_search_pokemon(self, interaction: discord.Interaction, current: str):
        return await self.autocomplete_pokemon_name(interaction, current)


async def setup(bot):
    await bot.add_cog(CrewPokemon(bot))
