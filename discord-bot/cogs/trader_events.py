import discord
from discord.ext import commands
from discord import app_commands
import datetime

class TraderEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="create_trader_events", description="Create monthly item trader events for the current month.")
    @app_commands.default_permissions(administrator=True)
    async def create_trader_events(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        trader_data = [
            {
                "day": 5,
                "location": "Goldburn City",
                "pokemon": "Druddigon",
                "items": [
                    ("TM044 Dragon Tail", 10000),
                    ("TM078 Dragon Claw", 25000),
                    ("TM100 Dragon Dance", 25000),
                    ("TM115 Dragon Pulse", 50000),
                    ("TM156 Outrage", 50000),
                    ("TM169 Draco Meteor", 75000),
                    ("TM200 Scale Shot", 75000),
                    ("TM222 Breaking Swipe", 100000),
                    ("Dragon Fang", 35000),
                    ("Dragon Scale", 10000),
                    ("Dratini Chest", 200000),
                ]
            },
            {
                "day": 12,
                "location": "Route 130",
                "pokemon": "Pidgeot",
                "items": [
                    ("TM014 Acrobatics", 20000),
                    ("TM205 Endeavor", 25000),
                    ("TM204 Double-Edge", 30000),
                    ("TM160 Hurricane", 35000),
                    ("TM065 Air Slash", 35000),
                    ("TM025 Facade", 50000),
                    ("TM197 Dual Wingbeat", 50000),
                    ("TM202 Pain Split", 100000),
                    ("Silk Scarf", 35000),
                    ("Soothe Bell", 10000),
                    ("Porygon Chest", 200000),
                ]
            },
            {
                "day": 19,
                "location": "Mt. Pyre 1F",
                "pokemon": "Gastly",
                "items": [
                    ("TM029 Hex", 20000),
                    ("TM224 Curse", 20000),
                    ("TM062 Foul Play", 35000),
                    ("TM094 Dark Pulse", 35000),
                    ("TM108 Crunch", 35000),
                    ("TM221 Throat Chop", 50000),
                    ("TM181 Knock Off", 65000),
                    ("TM114 Shadow Ball", 75000),
                    ("TM198 Poltergeist", 100000),
                    ("Spell Tag", 35000),
                    ("Dusk Stone", 10000),
                    ("Spiritomb Chest", 150000),
                ]
            },
            {
                "day": 26,
                "location": "Eterna Forest",
                "pokemon": "Roselia",
                "items": [
                    ("TM111 Giga Drain", 20000),
                    ("TM155 Frenzy Plant", 35000),
                    ("TM168 Solar Beam", 35000),
                    ("TM190 Solar Blade", 35000),
                    ("TM159 Leaf Storm", 50000),
                    ("TM137 Grassy Terrain", 55000),
                    ("TM020 Trailblaze", 65000),
                    ("TM194 Grassy Glide", 125000),
                    ("Miracle Seed", 35000),
                    ("Leaf Stone", 10000),
                    ("Larvesta Chest", 200000),
                ]
            },
        ]

        now = datetime.datetime.now(datetime.timezone.utc)
        year = now.year
        month = now.month

        created = []
        skipped = {
            "already passed": [],
            "already exists": [],
            "invalid date": []
        }

        existing_events = await interaction.guild.fetch_scheduled_events()

        for trader in trader_data:
            try:
                event_date = datetime.datetime(year, month, trader["day"], 0, 0, tzinfo=datetime.timezone.utc)
            except ValueError:
                skipped["invalid date"].append(f"{trader['day']}th")
                continue

            if event_date < now:
                skipped["already passed"].append(f"{trader['day']}th")
                continue

            name = f"Item Trader - {trader['location']}"
            if any(e.name == name and e.scheduled_start_time == event_date for e in existing_events):
                skipped["already exists"].append(f"{trader['day']}th")
                continue

            end_time = event_date + datetime.timedelta(hours=24)

            # Format items list
            item_lines = [f"{name:<25} – {price:,}" for name, price in trader["items"]]
            item_block = "```\n" + "\n".join(item_lines) + "\n```"

            await interaction.guild.create_scheduled_event(
                name=name,
                start_time=event_date,
                end_time=end_time,
                description=(
                    f"A Monthly Item Trader has appeared!\n\n"
                    f"📍 Location: **{trader['location']}**\n"
                    f"✨ Favorite Pokémon: **{trader['pokemon']}**\n\n"
                    f"Talk to the NPC with the correct Pokémon in your party (no item equipped).\n\n"
                    f"🛍️ Shop Inventory:\n{item_block}"
                ),
                location="In-game",
                entity_type=discord.EntityType.external,
                privacy_level=discord.PrivacyLevel.guild_only
            )

            created.append(str(trader["day"]))

        message = f"✅ Created events for: {', '.join(created) if created else 'None'}"
        for reason, days in skipped.items():
            if days:
                message += f"\n⚠️ Skipped ({reason}): {', '.join(days)}"

        await interaction.followup.send(message, ephemeral=True)

async def setup(bot):
    await bot.add_cog(TraderEvents(bot))