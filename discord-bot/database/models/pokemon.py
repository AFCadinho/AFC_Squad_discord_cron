from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.base import Base

if TYPE_CHECKING:
    from .lending import Loan

class Pokemon(Base):
    __tablename__ = "pokemon"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    ability: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    nature: Mapped[str] = mapped_column(sa.String(16), nullable=False)
    tier: Mapped[Optional[str]] = mapped_column(sa.String(16), nullable=True)
    discord_link: Mapped[Optional[str]] = mapped_column(sa.Text, nullable=True)
    always_stored: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, server_default=sa.false())
    loaned: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, server_default=sa.false())
    in_storage: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, server_default=sa.false())

    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )

    # reverse side for Loan.pokemon
    loans: Mapped[List["Loan"]] = relationship("Loan", back_populates="pokemon")

    def __repr__(self) -> str:
        return f"<Pokemon(name={self.name}, ability={self.ability}, nature={self.nature}, discord_link={self.discord_link})>"