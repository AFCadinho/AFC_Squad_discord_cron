import discord
import os
from discord import app_commands
from discord.ext import commands
from views import SignUpView

# Channel IDs from env (make sure they're ints)
SIGNUPS_CH = int(os.getenv("SIGNUPS_CH_ID", 0))
REPORTS_CH = int(os.getenv("REPORTS_CH_ID", 0))
VIDEO_CHANNEL = int(os.getenv("VIDEO_CH_ID", 0))
ANNOUNCEMENT_CH = int(os.getenv("ANNOUNCEMENTS_CH_ID", 0))
RULES_CH = int(os.getenv("RULES_CH_ID", 0))
SCHEDULING_CH = int(os.getenv("SCHEDULING_CH_ID", 0))


class TournamentInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        self.bot.add_view(SignUpView(self.bot))

    # === General Tournament Info ===
    @app_commands.command(name="general_tournament_info", description="Shows general tournament information")
    @app_commands.default_permissions(administrator=True)
    async def general_tournament_info(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🎮 How It Works",
            description=(
                "📝 **Sign-Ups**\n"
                f"• Sign up in <#{SIGNUPS_CH}> with `/sign_up`\n"
                "• Leave with `/unregister`\n\n"

                "⏳ **Rounds**\n"
                "• All tournaments are **Single Elimination**\n"
                "• Wait for the round announcement before playing your match\n\n"

                "📅 **Scheduling Matches**\n"
                "• After the round is announced, talk with your opponent and agree on a date and time\n"
                "• One of you uses `/schedule_match` to set it\n"
                "• You can play earlier, but never later than the schedule\n"
                "• Matches must be scheduled before **Wednesday (PBO in-game time)**\n\n"

                "🏁 **Report Matches**\n"
                f"• Winners report in <#{REPORTS_CH}> with `/report_win`\n"
                "• **Semifinals & Final:** include a **video link** (required)\n"
                "• **Earlier rounds:** video link is **optional**\n"
                "• Examples:\n"
                "  • Early rounds: `/report_win winner:@Username`\n"
                "  • Semis/Final: `/report_win winner:@Username video_link:https://...`\n\n"

                "🎥 **Video Proof & Visibility**\n"
                "- From the **Semifinals onward**, you **must** submit a video link (YouTube, Streamable, LimeWire, etc.)\n"
                "- **Semifinals & Final VODs will be shown to our members** in the server\n"
                "- For earlier rounds, recording is **recommended** but not required\n"
                "- Submitted early-round videos may be used for **coaching and match reviews** to help players improve\n\n"

                "📖 Recording Guide: [Click Here](https://discord.com/channels/1302588750630621184/1423922709108363285/1423935057382604883)\n"
                "📤 Upload Guide: [Click Here](https://discord.com/channels/1302588750630621184/1423922709108363285/1423944853762605086)\n\n"

                "⚖️ **Fair Play**\n"
                "• Be respectful\n"
                f"• Follow the rules in <#{RULES_CH}>"
            ),
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="tournament_rules", description="Shows the official tournament rules")
    @app_commands.default_permissions(administrator=True)
    async def tournament_rules(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="📜 Tournament Rules",
            description=(
                "⚖️ **General Conduct**\n"
                "• Be respectful — we are all friends here\n"
                "• No need to get angry if someone gets lucky\n\n"

                "📅 **Scheduling**\n"
                "• Matches must be scheduled before **Wednesday (PBO in-game time)**\n"
                "• If you do not schedule, staff will set a random time for you\n"
                "• If your opponent does not respond to scheduling, tell us by Wednesday. "
                "We will try to contact them. If they still do not answer, they are disqualified\n\n"

                "⏰ **Match Times**\n"
                "• If your opponent does not show up at the scheduled time, contact staff\n"
                "• We allow 15 minutes late. After that, they are disqualified\n"
                "• If both players do not show up, the winner will be decided by a coin flip\n\n"

                "🔌 **Disconnects**\n"
                "• In PBO, if you disconnect, the game closes and you lose instantly\n"
                "• Because of this, a disconnect always counts as a loss\n"
                "• Match History will decide who won\n\n"

                "📊 **Reporting Results**\n"
                f"• Winners must report the match result in the <#{REPORTS_CH}> channel\n"
                "• 🚨 Reporting a false score (claiming a win when you did not win) means instant disqualification\n\n"

                "🎥 **Video Proof (Semifinals & Finals)**\n"
                "• From the **Semifinals onward**, all matches **must be recorded** and a video link must be submitted\n"
                "• If no video proof is provided, the match **must be replayed**\n"
                "• Ensure your recording clearly shows both teams and the battle result\n\n"

                "⏳ **Rounds**\n"
                "• All tournaments are **Single Elimination**\n"
                "• Wait for the round announcement before playing your match\n\n"

                "⛔ **Pokémon Bans**\n"
                "• We follow the in-game Pokémon bans per tier\n"
                "• To see the list: open the **Ranked Ladder** (icon at the top left, next to the Pokédex)\n"
                "• In the Ranked Ladder window, click the **Bans** button (bottom right of the row)\n"
                "• Select **OverUsed (OU)** or **UnderUsed (UU)** to see the banned Pokémon list\n"
                "• Pokémon in these lists are not allowed in that tier\n\n"

                "📝 **Final Notes**\n"
                "• These rules cover the main cases, but they are not limited to this list\n"
                "• Rules may be updated or changed if needed during the tournament\n"
                "• Staff decisions are final\n\n"

                "🏆 These rules make sure the tournament is fair and smooth for everyone!"
            ),
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)

    # === Rewards Info ===

    @app_commands.command(name="tournament_rewards", description="Shows the rewards for the tournament")
    @app_commands.default_permissions(administrator=True)
    async def base_tournament_rewards(self, interaction: discord.Interaction):
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

    @app_commands.command(name="booster_tournament_rewards", description="Shows the increased rewards for the tournament")
    @app_commands.default_permissions(administrator=True)
    async def booster_tournament_rewards(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🎁 Tournament Rewards",
            description=(
                "🥇 **1st Place**\n"
                "• 👑 Special Discord role: **Champion** *(prestige, shown at the top until next tournament)*\n"
                "• 💎 750 Gems\n"
                "• 💰 600,000 Pokédollars\n\n"

                "🥈 **2nd Place**\n"
                "• 💎 450 Gems\n"
                "• 💰 350,000 Pokédollars\n\n"

                "🥉 **3rd Place**\n"
                "• 💎 200 Gems\n"
                "• 💰 175,000 Pokédollars\n\n"

                "🏅 **4th – 8th Place**\n"
                "• 💰 25,000 Pokédollars\n"
                "• 🧠 Crew Shop **TM of Choice**\n\n"

                "🎖️ **9th – 16th Place**\n"
                "• 💰 12,500 Pokédollars\n"
                "• 🧠 Crew Shop **Egg or Tutor**\n\n"

                "⚖️ Only **Rank 1** receives the Champion role.\n"
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
            ch: discord.TextChannel = await self.bot.fetch_channel(SIGNUPS_CH)
        if ch:
            view = SignUpView(self.bot)
            await ch.send(embed=self._signup_embed(), view=view)
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

    def _scheduling_reminder_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="📅 Scheduling Your Match",
            description=(
                "⚠️ **This channel is command-only.**\n"
                "Only use the slash command below after you and your opponent agreed on a time.\n\n"
                "• One of the players runs:\n"
                "`/schedule_match opponent:@Opponent round:<#> year:YYYY month:MM day:DD hour:HH minute:MM`\n\n"
                "📌 Example:\n"
                "`/schedule_match opponent:@Player2 round:1 year:2025 month:10 day:5 hour:19 minute:00`\n\n"
                "✅ Matches must be scheduled **before Wednesday (PBO in-game time)**\n"
                "✅ You may play earlier than the scheduled time, but not later."
            ),
            color=discord.Color.blue()
        )
        embed.set_footer(text="Only one schedule per match is needed.")
        return embed

    @app_commands.command(name="post_scheduling_embed", description="Post the scheduling help embed in the scheduling channel")
    @app_commands.default_permissions(administrator=True)
    async def post_scheduling_embed(self, interaction: discord.Interaction):
        ch = self.bot.get_channel(SCHEDULING_CH)
        if ch is None:
            ch = await self.bot.fetch_channel(SCHEDULING_CH)
        if ch:
            await ch.send(embed=self._scheduling_reminder_embed())
            await interaction.response.send_message("Scheduling embed posted.", ephemeral=True)
        else:
            await interaction.response.send_message("Couldn’t find the scheduling channel.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(TournamentInfo(bot))
