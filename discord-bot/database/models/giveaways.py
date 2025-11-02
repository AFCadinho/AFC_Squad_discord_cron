import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.base import Base
from datetime import datetime
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from .members import User

class GiveAway(Base):
    __tablename__ = "giveaways"

    id: Mapped[int] = mapped_column(primary_key=True)
    start_date: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    end_date: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    name: Mapped[str] = mapped_column(sa.Text, nullable=False)
    message_id: Mapped[int | None] = mapped_column(sa.BigInteger, unique=True)

    winner_id: Mapped[int | None] = mapped_column(
        sa.ForeignKey("users.id"), nullable=True)
    
    entries_row: Mapped[List["GiveAwayEntry"]] = relationship(
        back_populates="giveaway_link",
        cascade="all, delete-orphan"
    )

    winner: Mapped["User"] = relationship(
        back_populates="won_giveaways",
        foreign_keys="[GiveAway.winner_id]"
    )

class GiveAwayEntry(Base):
    __tablename__ = "giveaway_entries"
    __table_args__ = (
        sa.UniqueConstraint("giveaway_id", "user_id", name="uq_giveaway_entry_once"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    giveaway_id: Mapped[int] = mapped_column(
        sa.ForeignKey("giveaways.id", ondelete="CASCADE"),
        nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    giveaway_link: Mapped["GiveAway"] = relationship(
        back_populates="entries_row"
    )

    user_link: Mapped["User"] = relationship(
        back_populates="giveaways_row"
    )