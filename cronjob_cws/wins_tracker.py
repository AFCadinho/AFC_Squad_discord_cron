import requests
import os

from sqlalchemy import select, desc, asc
from database import Session
from models import User

STAFF_ANNOUNCEMENTS_CH = int(os.getenv("STAFF_ANNOUNCEMENTS_CH_ID", 0))
WINS_TRACKER_WEBHOOK = os.getenv("WEBHOOK_WINS", "")
INACTIVE_REPORT_WEBHOOK = os.getenv("INACTIVE_REPORT_WEBHOOK", "")


def get_members(session):

    stmt = (
        select(User)
        .where(
            User.is_active.is_(True)
        )
        .order_by(
            desc(User.crew_wars_wins),
            asc(User.username)
        )
    )
    return session.scalars(stmt).all()


def send_rapport(webhook, embed, ping=None):
    payload = {"embeds": [embed]}
    if ping:
        payload["content"] = ping

    response = requests.post(webhook, json=payload)
    response.raise_for_status()


def create_embed(members: list[User], title):

    if not members:
        description = "_No active members found._"
    else:
        lines = []
        for idx, member in enumerate(members, start=1):
            lines.append(
                f"**{idx}.** {member.username} — {member.crew_wars_wins} ")
        description = "\n".join(lines)

    embed = {
        "title": title,
        "description": description,
        "color": 0x5865F2,
    }

    return embed


def compare_wins(members: list[User]) -> list[User]:
    members_with_checkin: list[User] = []
    inactive_members: list[User] = []

    for member in members:
        if member.crew_wars_wins_checkin is not None:
            members_with_checkin.append(member)

    for member in members_with_checkin:
        if member.crew_wars_wins == member.crew_wars_wins_checkin:
            inactive_members.append(member)

    return inactive_members


def update_wins_checkin(members: list[User]):

    for member in members:
        if member.crew_wars_wins_checkin != member.crew_wars_wins:
            member.crew_wars_wins_checkin = member.crew_wars_wins


def run():
    send_inactive_report = True
    with Session.begin() as session:

        members = list(get_members(session))
        if len(members) == 0:
            print(f"No members found in DB")
            return

        # Inactive Members
        inactive_members = compare_wins(members)
        ping = "@everyone"
        if not inactive_members:
            print(f"No inactive members available")
            send_inactive_report = False

        # Insert data
        update_wins_checkin(members)

        # Send Data
        current_wins_title = "🏆 Crew Wars — Wins Leaderboard"
        current_wins_embed = create_embed(members, current_wins_title)

        inactive_users_title = "Inactive Users - List"
        inactive_users_embed = create_embed(
            inactive_members, inactive_users_title)

    send_rapport(WINS_TRACKER_WEBHOOK, current_wins_embed)
    if send_inactive_report:
        send_rapport(INACTIVE_REPORT_WEBHOOK, inactive_users_embed, ping=ping)


if __name__ == "__main__":
    run()
