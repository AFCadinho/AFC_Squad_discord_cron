from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.base import Base

if TYPE_CHECKING:
    from .members import User  

# Junction Table
tournament_participants = sa.Table(
    "tournament_participants",
    Base.metadata,
    sa.Column("tournament_id", sa.ForeignKey("tournaments.id"), primary_key=True),
    sa.Column("user_id", sa.ForeignKey("users.id"), primary_key=True),
)


class Tournament(Base):
    __tablename__ = "tournaments"

    id: Mapped[int] = mapped_column(primary_key=True)
    challonge_id: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    name: Mapped[str] = mapped_column(sa.Text, nullable=False)
    slug: Mapped[str] = mapped_column(sa.Text, nullable=False)
    url: Mapped[str] = mapped_column(sa.Text, nullable=False)
    ongoing: Mapped[bool] = mapped_column(sa.Boolean, server_default=sa.false())
    current_tournament: Mapped[bool] = mapped_column(sa.Boolean, server_default=sa.false())
    winner_id: Mapped[int] = mapped_column(sa.ForeignKey("users.id"), nullable=True)

    # One to many
    winner: Mapped["User"] = relationship(
        "User", foreign_keys=[winner_id], back_populates="won_tournaments"
    )

    # Many-to-many 
    participants: Mapped[list["User"]] = relationship(
        "User",
        secondary=tournament_participants,
        back_populates="tournaments",          # auto-creates User.tournaments
    )

    def __repr__(self) -> str:
        return (
            f"<Tournament(id={self.id}, name='{self.name}', slug='{self.slug}', "
            f"ongoing={self.ongoing}, current={self.current_tournament})>"
        )

