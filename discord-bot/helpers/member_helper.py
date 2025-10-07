from sqlalchemy import select
from database.models import User

def discord_id_to_member(session, discord_id):
        stmt = select(User).where(User.discord_id == discord_id)
        return session.scalars(stmt).first()