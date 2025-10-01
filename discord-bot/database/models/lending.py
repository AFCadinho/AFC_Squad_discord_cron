from typing import Optional, TYPE_CHECKING

from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.base import Base

if TYPE_CHECKING:
    from .members import User
    from .pokemon import Pokemon

class Loan(Base):
    __tablename__ = "loans"

    id: Mapped[int] = mapped_column(primary_key=True)
    pokemon_id: Mapped[int] = mapped_column(sa.ForeignKey("pokemon.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(sa.ForeignKey("users.id"), nullable=False)
    borrowed_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )
    returned_at: Mapped[Optional[datetime]] = mapped_column(
        sa.DateTime(timezone=True), nullable=True, default=None
    )

    user: Mapped["User"] = relationship("User", back_populates="loans")
    pokemon: Mapped["Pokemon"] = relationship("Pokemon", back_populates="loans")

    def __repr__(self) -> str:
        return f"<Loan(pokemon_id={self.pokemon_id}, user_id={self.user_id}, borrowed_at={self.borrowed_at})>"
