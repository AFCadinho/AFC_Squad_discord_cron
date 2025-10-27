from sqlalchemy import text
from database import Session
import requests
import os

WEBHOOK_URL = os.getenv("WEBHOOK_WINS", "")


def get_rows():
    query = """
            SELECT username, crew_wars_wins
            FROM users
            WHERE is_active = true
            ORDER BY crew_wars_wins DESC, username ASC
        """
    with Session() as session:
        result = session.execute(
            text(query)
        ).all()
        return result


def run():
    member_wins = get_rows()
    if not member_wins:
        description = "_No active members found._"
    else:
        lines = []
        for idx, (username, wins) in enumerate(member_wins, start=1):
            lines.append(f"**{idx}.** {username} — {wins} ")
        description = "\n".join(lines)

    embed = {
        "title": "🏆 Crew Wars — Wins Leaderboard",
        "description": description,
        "color": 0x5865F2,
    }
    payload = {"embeds": [embed]}
    response = requests.post(WEBHOOK_URL, json=payload)
    response.raise_for_status()


if __name__ == "__main__":
    run()
