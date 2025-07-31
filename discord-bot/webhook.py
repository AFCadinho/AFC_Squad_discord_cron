#!/usr/bin/env python3
import datetime
import requests

WEBHOOK_URL = "https://discord.com/api/webhooks/1388842342336958495/7VIupBtpB7ty-K6_V1ze_87eMXe72VEuZAQSTM0ZIb2oQb0V2OKrJnD2XVj6PyxmlvGv"

schedule = [
    {"day": "Monday", "time": "16:00", "tier": "UnderUsed"},
    {"day": "Wednesday", "time": "10:00", "tier": "UnderUsed"},
    {"day": "Wednesday", "time": "20:00", "tier": "OverUsed"},
    {"day": "Thursday", "time": "20:00", "tier": "UnderUsed"},
    {"day": "Saturday", "time": "03:00", "tier": "OverUsed"},
    {"day": "Sunday", "time": "01:00", "tier": "OverUsed"},
    {"day": "Sunday", "time": "18:00", "tier": "OverUsed"},
]

weekdays = {
    "Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
    "Friday": 4, "Saturday": 5, "Sunday": 6
}

def find_next_event():
    now = datetime.datetime.now(datetime.timezone.utc)
    upcoming = []
    for event in schedule:
        event_day = weekdays[event["day"]]
        event_time = datetime.datetime.strptime(event["time"], "%H:%M").time()
        event_date = now.date() + datetime.timedelta((event_day - now.weekday()) % 7)
        event_datetime = datetime.datetime.combine(event_date, event_time).replace(tzinfo=datetime.timezone.utc)

        if event_datetime < now:
            event_datetime += datetime.timedelta(days=7)

        upcoming.append((event_datetime, event["day"], event["time"], event["tier"]))

    return min(upcoming, key=lambda x: x[0])

def send_webhook_message():
    next_event = find_next_event()
    unix_timestamp = int(next_event[0].timestamp())
    tier = next_event[3]

    role_id = 1310224095228465214
    role_mention = f"<@&{role_id}>"

    message = {
        "content": (
            f"{role_mention} 🛡️ **Crew Wars starts <t:{unix_timestamp}:R>!**\n\n"
            f"**Tier:** {tier}\n\n"
            "Don't worry if your pvp team is not ready!\n"
            "You only need to do **1 match — win or lose — to receive full rewards**!\n"
            "Many **rare TMs and items** are exclusive to Crew Wars, so joining even once helps you build your PvP team faster. 💪\n\n"
            "Let’s fight together and earn those crew rewards! 🎯"
        ),
        "allowed_mentions": {
            "roles": [role_id]
        }
    }

    requests.post(WEBHOOK_URL, json=message)

if __name__ == "__main__":
    send_webhook_message()
