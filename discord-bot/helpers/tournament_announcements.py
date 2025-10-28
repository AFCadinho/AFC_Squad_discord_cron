from datetime import datetime, timedelta, time, timezone
import discord
import validators
import os

TOURNAMENT_PING = os.getenv("TOURNAMENT_PING_ID", 0)

def _next_weekday(dt: datetime, target_weekday: int) -> datetime:
    """Return the next date strictly after `dt` with weekday target_weekday (Mon=0..Sun=6)."""
    days_ahead = (target_weekday - dt.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    return dt + timedelta(days=days_ahead)


def create_winner_message(
    tournament_slug: str,
    first_user: discord.Member,
    second_user: discord.Member | None = None,
    third_user: discord.Member | None = None,
    fourth_user: discord.Member | None = None,
    vod_url: str | None = None,
) -> str:
    """Build a final winner announcement message that always uses mentions."""
    formatted_name = tournament_slug.replace("_", " ").title()
    bracket_url = f"https://challonge.com/{tournament_slug}"

    lines: list[str] = []
    lines.append(f"🏁 **{formatted_name}** has finished!\n")
    lines.append(f"👑 **Champion:** {first_user.mention}")
    if second_user:
        lines.append(f"🥈 **Runner-up:** {second_user.mention}")
    if third_user:
        lines.append(f"🥉 **Third Place:** {third_user.mention}")
    if fourth_user:
        lines.append(f"🎖️ **Fourth Place:** {fourth_user.mention}")

    if vod_url and validators.url(vod_url):
        lines.append(f"\n🎥 **Final VOD:** <{vod_url}>")

    lines.append(f"\n📊 [View the final bracket](<{bracket_url}>)\n")
    lines.append(
        "Thanks to everyone who participated — see you in the next tournament! 🎉\n@everyone")

    return "\n".join(lines)


def create_new_round_message(current_round: int, new_round: int, max_round: int, tournament_slug: str) -> str:
    """
    Announcement for a new round:
    - Schedule deadline: next Wednesday 12:00 UTC
    - Matches must be played before the Sunday after that Wednesday (23:59 UTC)
    """
    now_utc = datetime.now(timezone.utc)

    # Next Wednesday (weekday=2)
    next_wed_date = _next_weekday(now_utc, 2).date()
    schedule_deadline_dt = datetime.combine(
        next_wed_date, time(12, 0), tzinfo=timezone.utc)
    schedule_deadline_unix = int(schedule_deadline_dt.timestamp())

    # Sunday after that Wednesday (weekday=6) -> Wednesday + 4 days
    play_by_date = next_wed_date + timedelta(days=4)
    play_by_deadline_dt = datetime.combine(
        play_by_date, time(23, 59), tzinfo=timezone.utc)
    play_by_deadline_unix = int(play_by_deadline_dt.timestamp())

    formatted_name = tournament_slug.replace("_", " ").title()
    bracket_url = f"https://challonge.com/{tournament_slug}"

    if max_round - new_round == 1:
        display_round = " - Semi Finals"
    elif max_round == new_round:
        display_round = " - Finals"
    else:
        display_round = ""

    return (
        f"🏆 **{formatted_name}** — Round **{current_round}** - has finished!\n\n"
        f"🔥 **Round {new_round}{display_round}** has now started!\n\n"
        f"Private match channels have been created for this new round.\n"
        f"Please talk with your opponent **inside your match channel** and use the `/schedule_match` command to agree on a time for your battle.\n\n"
        f"⏰ **Deadline to Schedule Your Match:** <t:{schedule_deadline_unix}:F>\n"
        f"🎮 **Deadline to Play Your Match:** <t:{play_by_deadline_unix}:F>\n\n"
        f"📊 [View the updated tournament bracket](<{bracket_url}>)\n\n"
        f"Good luck to all remaining players!\n<@&{TOURNAMENT_PING}>"
    )
