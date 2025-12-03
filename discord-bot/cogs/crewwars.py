from discord import app_commands, Embed
from discord.ext import commands
import datetime
import discord

utc = datetime.timezone.utc


class CrewWars(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.schedule = [
            {"day": "Monday", "time": "16:00", "tier": "UnderUsed"},
            {"day": "Wednesday", "time": "10:00", "tier": "UnderUsed"},
            {"day": "Wednesday", "time": "20:00", "tier": "OverUsed"},
            {"day": "Thursday", "time": "20:00", "tier": "UnderUsed"},
            {"day": "Saturday", "time": "03:00", "tier": "OverUsed"},
            {"day": "Sunday", "time": "01:00", "tier": "OverUsed"},
            {"day": "Sunday", "time": "18:00", "tier": "OverUsed"},
        ]
        self.weekdays = {
            "Monday": 0,
            "Tuesday": 1,
            "Wednesday": 2,
            "Thursday": 3,
            "Friday": 4,
            "Saturday": 5,
            "Sunday": 6
        }

    def find_next_event(self):
        now = datetime.datetime.now(datetime.timezone.utc)
        upcoming = []
        for event in self.schedule:
            event_day = self.weekdays[event["day"]]
            event_time = datetime.datetime.strptime(
                event["time"], "%H:%M").time()
            event_date = now.date() + datetime.timedelta((event_day - now.weekday()) % 7)
            event_datetime = datetime.datetime.combine(
                event_date, event_time).replace(tzinfo=datetime.timezone.utc)

            if event_datetime < now:
                event_datetime += datetime.timedelta(days=7)

            upcoming.append(
                (event_datetime, event["day"], event["time"], event["tier"]))

        next_event = min(upcoming, key=lambda x: x[0])

        return next_event

    async def next_cws(self) -> discord.Embed:
        next_event = self.find_next_event()
        event_datetime = next_event[0]
        tier = next_event[3]

        # Discord dynamic timestamp
        unix_timestamp = int(event_datetime.timestamp())

        embed = Embed(
            title="🛡️ Next Crew Wars",
            description="The next Crew Wars event is:",
            color=0x5865F2
        )

        embed.add_field(
            name="🗓️ Date & Time",
            value=f"<t:{unix_timestamp}:F> — (<t:{unix_timestamp}:R>)",
            inline=False
        )

        embed.add_field(
            name="🏆 Tier",
            value=f"**{tier}**",
            inline=False
        )

        embed.set_footer(
            text="All times are automatically adjusted to your local timezone.")

        return embed

    
    @app_commands.command(name="crewwars", description="Show the next Crew Wars time and tier.")
    async def crewwars(self, interaction):
        embed = await self.next_cws()
        await interaction.response.send_message(embed=embed)
    
    
    @app_commands.command(name="ping_cws", description="Ping the Crew Wars role with time remaining")
    async def ping_cws(self, interaction: discord.Interaction):
        next_event = self.find_next_event()
        unix_timestamp = int(next_event[0].timestamp())
        tier = next_event[3]

        role_id = 1310224095228465214
        role_mention = f"<@&{role_id}>"

        message = (
            f"{role_mention} 🛡️ **Crew Wars starts <t:{unix_timestamp}:R>!**\n\n"
            f"**Tier:** {tier}\n\n"
            "Don't worry if your pvp team is not ready!\n"
            "You only need to do **1 match — win or lose — to receive full rewards**!\n"
            "Many **rare TMs and items** are exclusive to Crew Wars, so joining even once helps you build your PvP team faster. 💪\n\n"
            "Let’s fight together and earn those crew rewards! 🎯"
        )

        await interaction.response.send_message(
            content=message,
            allowed_mentions=discord.AllowedMentions(roles=True)
        )

    def get_next_events(self, count: int = 7):
        now = datetime.datetime.now(datetime.timezone.utc)
        upcoming = []

        for ev in self.schedule:
            event_day = self.weekdays[ev["day"]]
            event_time = datetime.datetime.strptime(ev["time"], "%H:%M").time()
            event_date = now.date() + datetime.timedelta((event_day - now.weekday()) % 7)
            event_dt = datetime.datetime.combine(event_date, event_time).replace(tzinfo=datetime.timezone.utc)

            if event_dt < now:
                event_dt += datetime.timedelta(days=7)

            upcoming.append((event_dt, ev["day"], ev["time"], ev["tier"]))

        # Keep cycling forward until we have enough events
        upcoming.sort(key=lambda x: x[0])
        results = []
        i = 0
        while len(results) < count:
            event_dt, day, time_str, tier = upcoming[i % len(upcoming)]
            # Add 7 days for each full rotation through the schedule
            event_dt = event_dt + datetime.timedelta(days=7 * (i // len(upcoming)))
            results.append((event_dt, day, time_str, tier))
            i += 1

        return results

    async def show_cws_schedule(self) -> discord.Embed:
        events = self.get_next_events(7)

        embed = Embed(
            title="🗓️ Next 7 Crew Wars",
            description="All times are automatically adjusted to your local timezone.",
            color=0x5865F2
        )

        for event_dt, day, _, tier in events:
            ts = int(event_dt.timestamp())
            embed.add_field(
                name=day,
                value=f"<t:{ts}:F> — (<t:{ts}:R>) • **{tier}**",
                inline=False
            )

        return embed
    
    @app_commands.command(name="crewwars_schedule", description="Show the next 7 Crew Wars events.")
    async def crewwars_schedule(self, interaction: discord.Interaction):
        embed = await self.show_cws_schedule()

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(CrewWars(bot))
