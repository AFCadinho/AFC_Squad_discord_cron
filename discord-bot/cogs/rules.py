import discord
from discord import app_commands, Embed
from discord.ext import commands
import json

class Rules(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def load_rules(self):
        with open("data/rules.json", "r", encoding="utf-8") as f:
            return json.load(f)

    
    @app_commands.command(
    name="update_rules_embed",
    description="Update the existing rules embed in place."
    )
    @app_commands.default_permissions(administrator=True)
    async def update_rules_embed(self, interaction: discord.Interaction, message_id: str):

        channel = interaction.channel
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message(
                "❌ This command can only be used in a text channel.",
                ephemeral=True
            )
            return

        try:
            message = await channel.fetch_message(int(message_id))
        except discord.NotFound:
            await interaction.response.send_message(
                "❌ Could not find the message. Make sure the message ID is correct.",
                ephemeral=True
            )
            return
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ I do not have permission to access the message in this channel.",
                ephemeral=True
            )
            return
        except discord.HTTPException:
            await interaction.response.send_message(
                "❌ An error occurred while trying to fetch the message.",
                ephemeral=True
            )
            return

        rules = self.load_rules()

        embed = message.embeds[0]  # Get the original embed

        # Clear old fields
        embed.clear_fields()

        emoji_map = {
            "Activity": "🎮",
            "Updating Wins": "🏆",
            "Absence": "🕒",
            "In-Game Behavior": "🗣️",
            "Leaving the Crew": "🚪",
            "Crew Storage": "📦"
        }

        # Re-add updated rules
        for section, text in rules.items():
            emoji = emoji_map.get(section, "📌")
            embed.add_field(name=f"{emoji} {section}", value=text, inline=False)

        # Edit the original message
        await message.edit(embed=embed)

        await interaction.response.send_message(
            "✅ Rules embed updated successfully!",
            ephemeral=True
        )

    
    
    @app_commands.command(name="rules", description="Display the crew rules in an embed")
    @app_commands.default_permissions(administrator=True)
    async def rules(self, interaction: discord.Interaction):
        if interaction.guild is None:
            await interaction.response.send_message(
                "❌ This command can only be used in a server.",
                ephemeral=True
            )
            return

        member = interaction.guild.get_member(interaction.user.id)
        if member is None or not member.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ You need to be a server admin to use this command.",
                ephemeral=True
            )
            return

        rules = self.load_rules()

        embed = Embed(
            title="📜 Crew Rules",
            description="Please read and follow these rules to help keep our crew fun and fair for everyone!",
            color=0x2ECC71
        )

        emoji_map = {
            "Activity": "🎮",
            "In-Game Behavior": "🗣️",
            "Leaving the Crew": "🚪",
            "Crew Storage": "📦"
        }

        for section, text in rules.items():
            emoji = emoji_map.get(section, "📌")
            embed.add_field(name=f"{emoji} {section}", value=text, inline=False)

        embed.set_footer(text="Thanks for being part of the crew! ❤️")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Rules(bot))
