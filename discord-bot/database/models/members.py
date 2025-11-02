from typing import Optional, List, TYPE_CHECKING
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.base import Base

if TYPE_CHECKING:
    from database.models.lending import Loan  # only for type hints
    from database.models.tournament import Tournament, TournamentParticipants
    from database.models.giveaways import GiveAway, GiveAwayEntry


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    discord_id: Mapped[int] = mapped_column(sa.BigInteger, nullable=False, unique=True)
    username: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    country: Mapped[Optional[str]] = mapped_column(sa.String(64), nullable=True)
    is_active: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, server_default=sa.true())
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)

    pvp_experience: Mapped[str] = mapped_column(sa.Text, nullable=False, server_default="novice")
    timezone_name: Mapped[str] = mapped_column(sa.Text, nullable=True)
    crew_wars_wins: Mapped[int] = mapped_column(sa.Integer, default=0, server_default=sa.text("0"))

    loans: Mapped[List["Loan"]] = relationship("Loan", back_populates="user")

    # Many to One
    won_tournaments: Mapped[List["Tournament"]] = relationship(
        foreign_keys="Tournament.winner_id",
        back_populates="winner",
    )

    # Many to Many
    tournament_rows: Mapped[List["TournamentParticipants"]] = relationship(
        back_populates="user_link",
        cascade="all"
    )

    giveaways_row: Mapped[List["GiveAwayEntry"]] = relationship(
        back_populates="user_link",
        cascade="all"
    )

    won_giveaways: Mapped[List["GiveAway"]] = relationship(
        foreign_keys="GiveAway.winner_id",
        back_populates="winner",
    )


    def __repr__(self) -> str:
        return f"<User(discord_id={self.discord_id}, username={self.username}, country_timezone={self.country})>"
