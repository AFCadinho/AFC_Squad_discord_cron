from typing import Optional
from datetime import datetime

import sqlalchemy as sa
import os

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from sqlalchemy import create_engine

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://user:password@localhost:5432/dbname"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
Session = sessionmaker(bind=engine)

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    discord_id: Mapped[int] = mapped_column(sa.BigInteger, nullable=False, unique=True)
    username: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    country: Mapped[Optional[str]] = mapped_column(sa.String(64), nullable=True)
    is_active: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, server_default=sa.true())
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    crew_wars_wins: Mapped[int] = mapped_column(sa.Integer, default=0, server_default=sa.text("0"))
    crew_wars_wins_checkin: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)

    def __repr__(self) -> str:
        return f"<User(discord_id={self.discord_id}, username={self.username}, country_timezone={self.country})>"
