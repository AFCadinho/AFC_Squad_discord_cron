from typing import Optional, List, TYPE_CHECKING
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.base import Base

if TYPE_CHECKING:
    from database.models.lending import Loan  # only for type hints
    from database.models.tournament import Tournament, TournamentParticipants


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    discord_id: Mapped[int] = mapped_column(sa.BigInteger, nullable=False, unique=True)
    username: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    country_timezone: Mapped[Optional[str]] = mapped_column(sa.String(64))
    is_active: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, server_default=sa.true())
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)

    pvp_experience: Mapped[str] = mapped_column(sa.Text, nullable=False, server_default="novice")

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


    def __repr__(self) -> str:
        return f"<User(discord_id={self.discord_id}, username={self.username}, country_timezone={self.country_timezone})>"
