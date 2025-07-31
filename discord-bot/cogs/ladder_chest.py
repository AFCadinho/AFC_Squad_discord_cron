import discord
from discord.ext import commands
from discord import app_commands
import datetime
import io
from generate_team_image import fetch_pokemon_sprite

class LadderChest(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ultra_rotation = {
            (1, 2, 3): "Poipole",
            (4, 5, 6): "Celesteela",
            (7, 8, 9): "Buzzwole",
            (10, 11, 12): "Magearna"
        }
        self.legendary_rotation = {
            (1, 2, 3): "Meltan",
            (4, 5, 6): "Zeraora",
            (7, 8, 9): "Volcanion",
            (10, 11, 12): "Keldeo (1st place gets Keldeo-Resolute)"
        }

    def get_current_rotation(self, rotation):
        month = datetime.datetime.utcnow().month
        for months, pokemon in rotation.items():
            if month in months:
                return pokemon, months
        return None, None

    @app_commands.command(name="ultra", description="Show the current Ultra Rare Ladder Chest Pokémon and full seasonal rotation")
    async def ultra(self, interaction: discord.Interaction):
        current_pokemon, months = self.get_current_rotation(self.ultra_rotation)
        month_name = datetime.datetime.utcnow().strftime("%B")

        month_labels = {
            (1, 2, 3): "January – February – March",
            (4, 5, 6): "April – May – June",
            (7, 8, 9): "July – August – September",
            (10, 11, 12): "October – November – December"
        }

        summary_lines = [
            f"• **{label}:** {pokemon}"
            for months_tuple, pokemon in self.ultra_rotation.items()
            for label in [month_labels[months_tuple]]
        ]

        embed = discord.Embed(
            title="🧬 Ultra Rare Ladder Chest Pokémon",
            description=f"🔹 **Current Pokémon:** {current_pokemon}\n_(_Available {month_labels[months]}_)_",
            color=discord.Color.purple()
        )

        embed.set_footer(text=f"Current month: {month_name}")
        embed.add_field(name="🗓️ Full Rotation", value="\n".join(summary_lines), inline=False)

        sprite = fetch_pokemon_sprite(current_pokemon)
        if sprite:
            with io.BytesIO() as image_binary:
                sprite.save(image_binary, format='PNG')
                image_binary.seek(0)
                file = discord.File(fp=image_binary, filename="sprite.png")
                embed.set_thumbnail(url="attachment://sprite.png")
                await interaction.response.send_message(embed=embed, file=file)
        else:
            await interaction.response.send_message(embed=embed)

    @app_commands.command(name="legend", description="Show the current Legendary Ladder Chest Pokémon and full seasonal rotation")
    async def legend(self, interaction: discord.Interaction):
        current_pokemon, months = self.get_current_rotation(self.legendary_rotation)
        month_name = datetime.datetime.utcnow().strftime("%B")

        month_labels = {
            (1, 2, 3): "January – February – March",
            (4, 5, 6): "April – May – June",
            (7, 8, 9): "July – August – September",
            (10, 11, 12): "October – November – December"
        }

        summary_lines = [
            f"• **{label}:** {pokemon}"
            for months_tuple, pokemon in self.legendary_rotation.items()
            for label in [month_labels[months_tuple]]
        ]

        embed = discord.Embed(
            title="✨ Legendary Ladder Chest Pokémon",
            description=f"🔹 **Current Pokémon:** {current_pokemon}\n_(_Available {month_labels[months]}_)_",
            color=discord.Color.gold()
        )

        embed.set_footer(text=f"Current month: {month_name}")
        embed.add_field(name="🗓️ Full Rotation", value="\n".join(summary_lines), inline=False)

        sprite = fetch_pokemon_sprite(current_pokemon)
        if sprite:
            with io.BytesIO() as image_binary:
                sprite.save(image_binary, format='PNG')
                image_binary.seek(0)
                file = discord.File(fp=image_binary, filename="sprite.png")
                embed.set_thumbnail(url="attachment://sprite.png")
                await interaction.response.send_message(embed=embed, file=file)
        else:
            await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(LadderChest(bot))
