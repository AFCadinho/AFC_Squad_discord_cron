import discord
import os
from discord import app_commands
from discord.ext import commands

SIGNUPS_CH_ID = int(os.getenv("SIGNUPS_CH_ID", 0))
REPORTS_CH_ID = int(os.getenv("REPORTS_CH_ID", 0))

class TournamentInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="general_tournament_info", description="Shows general tournament information")
    @app_commands.default_permissions(administrator=True)
    async def general_tournament_info(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🎮 How It Works",
            description=(
                "🗓️ **One tournament = one month**\n"
                "📖 **4 rounds total** → 1 round every week\n"
                "👥 **You play one opponent each week**\n"
                "📌 **You and your opponent plan the match** (any time during that week)\n\n"
                f"📝 **Sign up in <#{SIGNUPS_CH_ID}> using `/sign_up`**\n"
                f"🏁 **The winner will report the result in <#{REPORTS_CH_ID}>**\n"
                " • The report must say *who won*\n"
                " • The report must include a **video link of the battle**\n\n"
                "📺 **Everyone must provide a video link, so all matches are visible and fair**\n"
                "👨‍⚖️ **Moderators will update the official bracket on Challonge.**\n\n"
                "### 🎥 How to Record & Upload\n"
                "- On **PC**:\n"
                "  • Record with [Veed.io Screen Recorder](https://www.veed.io/tools/screen-recorder) (no install needed)\n"
                "  • Upload the video to [Streamable](https://streamable.com/) and share the link\n\n"
                "- On **Phone**:\n"
                "  • Use built-in screen recording (iOS/Android)\n"
                "  • Upload to [Streamable](https://streamable.com/) and share the link\n\n"
                "⚠️ Free Streamable accounts keep videos online for **3 months** — more than enough for the tournament."
            ),
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="tournament_rewards", description="Shows the rewards for the tournament")
    @app_commands.default_permissions(administrator=True)
    async def tournament_rewards(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🎁 Rewards",
            description=(
                "🥇 **1st Place**\n"
                "• 👑 Special Discord role: **Champion** (prestige, shown at the top until next tournament)\n"
                "• 💎 500 Gems\n"
                "• 💰 250,000 Pokédollars\n\n"
                "🥈 **2nd Place**\n"
                "• 💎 250 Gems\n"
                "• 💰 100,000 Pokédollars\n\n"
                "🥉 **3rd Place**\n"
                "• 💎 100 Gems\n"
                "• 💰 50,000 Pokédollars\n\n"
                "⚖️ Only **Rank 1** gets the Champion role.\n"
                "Rewards may be adjusted in future tournaments."
            ),
            color=discord.Color.gold()
        )
        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(TournamentInfo(bot))