from typing import TYPE_CHECKING, List

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from database.base import Base

if TYPE_CHECKING:
    from .members import User
    

class TournamentMatches(Base):
    __tablename__ = "tournament_matches"
    __table_args__ = (
        sa.UniqueConstraint(
            "tournament_id", "challonge_id",
            name="uq_tm_t_chid"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tournament_id: Mapped[int] = mapped_column(sa.ForeignKey(
        "tournaments.id", ondelete="CASCADE"), nullable=False)
    participant1_id: Mapped[int | None] = mapped_column(sa.ForeignKey(
        "tournament_participants.id", ondelete="SET NULL"), nullable=True)
    participant2_id: Mapped[int | None] = mapped_column(sa.ForeignKey(
        "tournament_participants.id", ondelete="SET NULL"), nullable=True)
    challonge_id: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    round: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    scheduled_datetime: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    completed: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, server_default=sa.false())
    winner_participant_id: Mapped[int  | None] = mapped_column(
        sa.ForeignKey("tournament_participants.id", ondelete="SET NULL"),
        nullable=True)
    score: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    battle_url: Mapped[str] = mapped_column(sa.Text, nullable=True)

    # Relationship
    tournament_link: Mapped["Tournament"] = relationship(
        back_populates="matches_rows"
    )

    participant1_link: Mapped["TournamentParticipants"] = relationship(
        foreign_keys=[participant1_id],
        back_populates="matches_row_p1"
    )

    participant2_link: Mapped["TournamentParticipants"] = relationship(
        foreign_keys=[participant2_id],
        back_populates="matches_row_p2"
    )

    winner_link: Mapped["TournamentParticipants"] = relationship(
        foreign_keys=[winner_participant_id]
    )

    def __repr__(self) -> str:
        return (
            "<TournamentMatch("
            f"id={self.id}, "
            f"tournament_id={self.tournament_id}, "
            f"round={self.round}, "
            f"challonge_id={self.challonge_id}, "
            f"participant1_id={self.participant1_id}, "
            f"participant2_id={self.participant2_id}, "
            f"winner_participant_id={self.winner_participant_id}, "
            f"completed={self.completed}, "
            f"score={repr(self.score)}, "
            f"scheduled_datetime={self.scheduled_datetime}"
            ")>"
        )


class TournamentParticipants(Base):
    __tablename__ = "tournament_participants"
    __table_args__ = (
        sa.UniqueConstraint(
            "tournament_id", "user_id"
        ),
        sa.UniqueConstraint(
            "tournament_id", "challonge_id"
        )
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tournament_id: Mapped[int] = mapped_column(sa.ForeignKey(
        "tournaments.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(sa.ForeignKey(
        "users.id", ondelete="CASCADE"), nullable=False)
    challonge_id: Mapped[int] = mapped_column(sa.Integer, nullable=True)

    tournament_link: Mapped["Tournament"] = relationship(
        back_populates="participant_rows"
    )

    user_link: Mapped["User"] = relationship(
        back_populates="tournament_rows"
    )

    matches_row_p1: Mapped[List["TournamentMatches"]] = relationship(
        foreign_keys="TournamentMatches.participant1_id",
        back_populates="participant1_link",
    )

    matches_row_p2: Mapped[List["TournamentMatches"]] = relationship(
        foreign_keys="TournamentMatches.participant2_id",
        back_populates="participant2_link",
    )

    def __repr__(self) -> str:
        return (
            "<TournamentParticipant("
            f"id={self.id}, "
            f"tournament_id={self.tournament_id}, "
            f"user_id={self.user_id}, "
            f"challonge_id={self.challonge_id}"
            ")>"
        )


class Tournament(Base):
    __tablename__ = "tournaments"

    id: Mapped[int] = mapped_column(primary_key=True)
    challonge_id: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    name: Mapped[str] = mapped_column(sa.Text, nullable=False)
    slug: Mapped[str] = mapped_column(sa.Text, nullable=False)
    url: Mapped[str] = mapped_column(sa.Text, nullable=False)
    ongoing: Mapped[bool] = mapped_column(
        sa.Boolean, server_default=sa.false())
    current_tournament: Mapped[bool] = mapped_column(
        sa.Boolean, server_default=sa.false())
    winner_id: Mapped[int] = mapped_column(
        sa.ForeignKey("users.id"), nullable=True)


    winner: Mapped["User"] = relationship(
        back_populates="won_tournaments"
    )

    matches_rows: Mapped[List["TournamentMatches"]] = relationship(
        back_populates="tournament_link",
        cascade="all, delete-orphan"
    )

    participant_rows: Mapped[List["TournamentParticipants"]] = relationship(
        back_populates="tournament_link",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<Tournament(id={self.id}, name='{self.name}', slug='{self.slug}', "
            f"ongoing={self.ongoing}, current={self.current_tournament}, url={self.url} )>"
        )
