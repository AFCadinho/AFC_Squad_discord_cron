import discord
import os
from discord import app_commands
from discord.ext import commands

# Channel IDs from env (make sure they're ints)
SIGNUPS_CH = int(os.getenv("SIGNUPS_CH_ID", 0))
REPORTS_CH = int(os.getenv("REPORTS_CH_ID", 0))
VIDEO_CHANNEL = int(os.getenv("VIDEO_CH_ID", 0))
ANNOUNCEMENT_CH = int(os.getenv("ANNOUNCEMENTS_CH_ID", 0))


class TournamentInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # === General Tournament Info ===
    @app_commands.command(name="general_tournament_info", description="Shows general tournament information")
    @app_commands.default_permissions(administrator=True)
    async def general_tournament_info(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🎮 How It Works",
            description=(
                "🗓️ **One tournament = one month**\n"
                "📖 **4 rounds total** → 1 round every week\n"
                "👥 **You play one opponent each week**\n\n"
                "🚦 **Please don’t start a round on your own.**\n"
                f"Wait for us to announce the official start of each round in <#{ANNOUNCEMENT_CH}> "
                "before playing your match.\n\n"
                "📌 **You and your opponent plan the match** (any time during that week, after it’s announced)\n\n"
                f"📝 **Sign up in <#{SIGNUPS_CH}> using `/sign_up`**\n"
                f"🏁 **Report wins in <#{REPORTS_CH}> using `/report_win`**\n"
                " • **You must pass the winner _Discord account_ and a _video link_**\n"
                " • Example: `/report_win winner: @Username video_link: https://...`\n"
                " • ❌ **Reports without video proof are rejected and must be redone**\n\n"
                "👨‍⚖️ **Moderators will update the official bracket on Challonge.**\n\n"
                "### 🎥 How to Record & Upload\n"
                "- On **PC**:\n"
                "  • Record with a screen recorder (e.g. Veed.io)\n"
                "  • Upload to Streamable/YouTube and share the link\n\n"
                "- On **Phone**:\n"
                "  • Use built-in screen recording (iOS/Android)\n"
                "  • Upload to Streamable/YouTube and share the link\n"
            ),
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)

    # === Rewards Info ===
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

    # === Helper: Sign-up Embed ===
    def _signup_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="📝 Tournament Sign-Up",
            description=(
                "Welcome to the sign-up channel!\n\n"
                "⚠️ **This channel is command-only.**\n"
                "Please do not chat here — use the commands below:\n\n"
                "• Use **`/sign_up`** to register for the tournament.\n"
                "• If you change your mind, use **`/unregister`** to withdraw.\n\n"
                "✅ Once the tournament starts, you’ll be entered into the bracket."
            ),
            color=discord.Color.blue()
        )
        embed.set_footer(
            text="Sign up only if you’re sure you can play this month. Good luck!")
        return embed

    def _reports_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="🏆 Reporting Match Results",
            description=(
                "This is where you report your completed matches.\n\n"
                "⚠️ **This channel is command-only.**\n"
                "Please do not chat here — only use the slash command below:\n\n"
                "After finishing your match:\n"
                "• The **winner** must run:\n"
                "  **`/report_win winner: @Winner video_link: <URL>`**\n\n"
                "⚠️ Important:\n"
                "• You **must** include the winner’s Discord account and a valid **video link**.\n"
                "• Example: `/report_win winner: @Player1 video_link: https://streamable.com/abcd`\n"
                "• ❌ Reports without video proof will be rejected and must be **redone**."
            ),
            color=discord.Color.orange()
        )
        embed.set_footer(
            text="Only one report per match is needed — made by the winner.")
        return embed

    # === Admin Command: Post Sign-up Embed ===

    @app_commands.command(name="post_signup_embed", description="Post the sign-up help embed in the sign-up channel")
    @app_commands.default_permissions(administrator=True)
    async def post_signup_embed(self, interaction: discord.Interaction):
        ch = self.bot.get_channel(SIGNUPS_CH)
        if ch is None:
            ch = await self.bot.fetch_channel(SIGNUPS_CH)
        if ch:
            await ch.send(embed=self._signup_embed())
            await interaction.response.send_message("Sign-up embed posted.", ephemeral=True)
        else:
            await interaction.response.send_message("Couldn’t find the sign-up channel.", ephemeral=True)

    # === Admin Command: Post Reports Embed ===
    @app_commands.command(name="post_reports_embed", description="Post the reporting help embed in the reports channel")
    @app_commands.default_permissions(administrator=True)
    async def post_reports_embed(self, interaction: discord.Interaction):
        ch = self.bot.get_channel(REPORTS_CH)
        if ch is None:
            ch = await self.bot.fetch_channel(REPORTS_CH)
        if ch:
            await ch.send(embed=self._reports_embed())
            await interaction.response.send_message("Reports embed posted.", ephemeral=True)
        else:
            await interaction.response.send_message("Couldn’t find the reports channel.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(TournamentInfo(bot))
