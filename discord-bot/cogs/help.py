from discord.ext import commands
from discord import app_commands, Interaction, Embed

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="Show all available slash commands")
    async def help(self, interaction: Interaction):
        embed = Embed(
            title="📖 Slash Command Help",
            description="Here are the available slash commands:\n\n",
            color=0x5865F2
        )

        for command in self.bot.tree.get_commands():
            # Hide admin-only commands from non-admins
            if command.default_permissions and not interaction.user.guild_permissions.administrator:
                continue

            embed.description += f"`/{command.name}` — {command.description or 'No description'}\n"

        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Help(bot))
