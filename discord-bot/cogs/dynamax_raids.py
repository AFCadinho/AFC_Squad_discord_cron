from discord import app_commands, Embed
from discord.ext import commands
import datetime
import discord

utc = datetime.timezone.utc

class DynamaxRaids(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.schedule = [
            {"day": "Wednesday", "time": "10:00", "label": "Morning"},
            {"day": "Wednesday", "time": "18:00", "label": "Evening"},
            {"day": "Friday", "time": "01:00", "label": "Night"},
            {"day": "Friday", "time": "16:00", "label": "Evening"},
            {"day": "Saturday", "time": "10:00", "label": "Morning"},
            {"day": "Saturday", "time": "16:00", "label": "Afternoon"},
            {"day": "Sunday", "time": "03:00", "label": "Night"},
            {"day": "Sunday", "time": "20:00", "label": "Evening"},
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
            event_time = datetime.datetime.strptime(event["time"], "%H:%M").time()
            event_date = now.date() + datetime.timedelta((event_day - now.weekday()) % 7)
            event_datetime = datetime.datetime.combine(event_date, event_time).replace(tzinfo=datetime.timezone.utc)

            if event_datetime < now:
                event_datetime += datetime.timedelta(days=7)

            upcoming.append((event_datetime, event["day"], event["time"], event["label"]))

        next_event = min(upcoming, key=lambda x: x[0])
        return next_event

    @app_commands.command(name="dynamax", description="Show the next Dynamax Raid time.")
    async def dynamax(self, interaction: discord.Interaction):
        next_event = self.find_next_event()
        event_datetime = next_event[0]
        label = next_event[3]
        unix_timestamp = int(event_datetime.timestamp())

        embed = Embed(
            title="✨ Next Dynamax Raid",
            description="The next Dynamax Raid will begin at:",
            color=0xFF2E93
        )
        embed.add_field(
            name="🗓️ Date & Time",
            value=f"<t:{unix_timestamp}:F> — (<t:{unix_timestamp}:R>)",
            inline=False
        )
        embed.add_field(
            name="🕒 Period",
            value=f"**{label}**",
            inline=False
        )
        embed.set_footer(text="All times are shown in your local timezone.")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="ping_dynamax", description="Ping the Dynamax role with time remaining")
    async def ping_dynamax(self, interaction: discord.Interaction):
        next_event = self.find_next_event()
        event_datetime = next_event[0]
        unix_timestamp = int(event_datetime.timestamp())
        label = next_event[3]

        role_id = 1310224206637830206  # Dynamax role
        role_mention = f"<@&{role_id}>"

        await interaction.response.send_message(
            content=f"{role_mention} Dynamax Raid starts <t:{unix_timestamp}:R>! ✨ Time: **{label}**",
            allowed_mentions=discord.AllowedMentions(roles=True)
        )

async def setup(bot):
    await bot.add_cog(DynamaxRaids(bot))
