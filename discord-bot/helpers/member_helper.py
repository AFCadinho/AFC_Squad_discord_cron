from sqlalchemy import select
from database.models import User, TournamentParticipants


def discord_id_to_member(session, discord_id):
    stmt = select(User).where(User.discord_id == discord_id)
    return session.scalars(stmt).first()


def participant_id_to_member(session, tournament_id, participant_id):
    stmt = (
        select(User)
        .join(TournamentParticipants, TournamentParticipants.user_id == User.id)
        .where(
            TournamentParticipants.tournament_id == tournament_id,
            TournamentParticipants.id == participant_id
        )
    )
    return session.scalars(stmt).first()