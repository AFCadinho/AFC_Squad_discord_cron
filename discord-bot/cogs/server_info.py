import discord
from discord import app_commands, Embed
from discord.ext import commands
from views import ServerToolsView


class ServerInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        self.bot.add_view(ServerToolsView(self.bot))

    # -------------------------
    # Overview Section
    # -------------------------

    @app_commands.command(
        name="crew_overview",
        description="Display the overview embed for the server-info channel."
    )
    @app_commands.default_permissions(administrator=True)
    async def overview(self, interaction: discord.Interaction):

        overview_embed = Embed(
            title="AFC Squad — PBO Crew",
            description=(
                "**Welcome to the AFC Squad — Pokémon Blaze Online Crew.**\n"
                "This channel provides general information about our crew and our Discord, "
                "as well as a few useful tools to help you navigate everything easily.\n\n"
                "**Topics in this channel:**\n"
                "• About Us\n"
                "• Crew Roles & Progression\n"
                "• Prospect Branch (Second Crew)\n"
                "• Useful Tools"
            ),
            color=discord.Color.blue(),
        )

        await interaction.response.send_message(embed=overview_embed)

    # -------------------------
    # About Us Section
    # -------------------------

    @app_commands.command(
        name="crew_about_us",
        description="Display an embed with the About Us information."
    )
    @app_commands.default_permissions(administrator=True)
    async def about_us(self, interaction: discord.Interaction):

        about_embed = Embed(
            title="About Us",
            description=(
                "**AFC Squad is a PvP–focused crew with long-standing roots in competitive Pokémon.**\n"
                "We originally formed in **PokeOne**, where we dominated the PvP scene and built the foundation of our community.\n\n"
                "We created our PBO crew around the game's release in **May 2021**, but due to **low development and lack of content**, "
                "we left the game shortly after.\n\n"
                "In **early 2025**, we made our official return — stronger and more organized than ever.\n"
                "Since the **summer of 2025**, we have been **dominating Crew Wars**, establishing ourselves as one of the top competitive crews in PBO.\n\n"
                "**Our goal is simple:** remain at the top and continue to grow together."
            ),
            color=discord.Color.blue(),
        )

        await interaction.response.send_message(embed=about_embed)

    @app_commands.command(
        name="crew_roles",
        description="Display an embed explaining all crew roles and progression."
    )
    @app_commands.default_permissions(administrator=True)
    async def crew_roles(self, interaction: discord.Interaction):

        roles_embed = Embed(
            title="Crew Roles & Progression",
            description=(
                "This section explains what each crew role means and how progression works within AFC Squad."
            ),
            color=discord.Color.blue(),
        )

        roles_embed.add_field(
            name="🏆 AFC Champion",
            value=(
                "Winner of our most recent **AFC Crew Tournament**. "
                "This title is exclusive and passes on to the latest champion."
            ),
            inline=False,
        )

        roles_embed.add_field(
            name="🐐 Crew Wars GOATS",
            value=(
                "Players with the **top 10 Crew Wars wins of the current month**. "
                "A monthly rotating role highlighting our strongest performers."
            ),
            inline=False,
        )

        roles_embed.add_field(
            name="🔥 AFC Core",
            value=(
                "Members who almost always show up to Crew Wars and events. "
                "Reliable players who embody the true **AFC Squad spirit**."
            ),
            inline=False,
        )

        roles_embed.add_field(
            name="⚔ Commanders",
            value=(
                "Our staff team. They manage recruitment, events, storage and moderation."
            ),
            inline=False,
        )

        roles_embed.add_field(
            name="💬 Crew Member",
            value=(
                "Fully accepted members of the crew who have shown dedication and consistency. "
                "Considered part of the main roster."
            ),
            inline=False,
        )

        roles_embed.add_field(
            name="🎯 Recruit",
            value=(
                "Players who have been accepted into the crew but still need to "
                "prove their dedication and activity before becoming full members."
            ),
            inline=False,
        )

        roles_embed.add_field(
            name="🌱 AFC Prospect",
            value=(
                "New players who are eager to join but are **not in the main crew yet**. "
                "They must finish the storyline and build their first PvP teams before promotion to Recruit."
            ),
            inline=False,
        )

        roles_embed.add_field(
            name="➡ Progression",
            value="🌱 **Prospect** → 🎯 **Recruit** → 💬 **Crew Member** → 🔥 **AFC Core** "
            "+ titles like 🐐 **GOATS** and 🏆 **Champion** for top performers.",
            inline=False,
        )

        await interaction.response.send_message(embed=roles_embed)

    @app_commands.command(
        name="crew_second_branch",
        description="Display an embed explaining our second crew for new players."
    )
    @app_commands.default_permissions(administrator=True)
    async def crew_second_branch(self, interaction: discord.Interaction):

        announcement_link = "https://discord.com/channels/1302588750630621184/1302589145570345011/1443969443201024162"

        branch_embed = Embed(
            title="AFC Prospect Branch (Second Crew)",
            description=(
                "**We run a secondary crew for players who want to join AFC Squad but are not PvP–ready yet.**\n"
                "This includes players who haven't finished the storyline, haven't built PvP teams, or are still learning the game.\n\n"
                "Prospects receive **the same Discord perks** as main crew members.\n\n"
                "To keep everyone connected, both crews use a shared private in-game chat.\n\n"
                f"👉 **How to join the in-game chat:**\n"
                f"<{announcement_link}>\n\n"
                "Once a Prospect finishes the storyline and builds their first PvP teams, "
                "they are promoted into the **main AFC Squad crew**."
            ),
            color=discord.Color.blue(),
        )

        await interaction.response.send_message(embed=branch_embed)

    @app_commands.command(
        name="crew_tools",
        description="Display an embed with buttons for useful crew tools."
    )
    @app_commands.default_permissions(administrator=True)
    async def crew_tools(self, interaction: discord.Interaction):

        tools_embed = Embed(
            title="Useful Tools",
            description=(
                "These tools help you stay up-to-date with Crew Wars and important in-game mechanics.\n\n"
                "**Next CWS** – Shows the **next upcoming Crew Wars time**.\n"
                "**CWS Schedule** – Displays the **full Crew Wars schedule** for the week.\n"
                "**Tide** – Shows whether it is currently **High Tide** or **Low Tide** in-game."
            ),
            color=discord.Color.blue(),
        )

        view = ServerToolsView(self.bot)

        await interaction.response.send_message(embed=tools_embed, view=view)


async def setup(bot):
    await bot.add_cog(ServerInfo(bot))
