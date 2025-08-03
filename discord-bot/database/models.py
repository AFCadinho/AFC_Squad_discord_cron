import os
from datetime import datetime
from typing import Optional, List

import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Mapped, mapped_column, relationship
from dotenv import load_dotenv

load_dotenv()

# Use the env var (inside Docker: host=postgres). Fallback is just for ad-hoc local tests.
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://user:password@localhost:5432/dbname"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
Session = sessionmaker(engine)


class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    discord_id: Mapped[int] = mapped_column(sa.BigInteger, nullable=False, unique=True)
    username: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    country_timezone: Mapped[Optional[str]] = mapped_column(sa.String(64), nullable=True)
    is_active: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, server_default=sa.true())
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )

    # reverse side for Loan.user
    loans: Mapped[List["Loan"]] = relationship(back_populates="user")

    def __repr__(self) -> str:
        return f"<User(discord_id={self.discord_id}, username={self.username}, country_timezone={self.country_timezone})>"

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
    loans: Mapped[List["Loan"]] = relationship(back_populates="pokemon")

    def __repr__(self) -> str:
        return f"<Pokemon(name={self.name}, ability={self.ability}, nature={self.nature}, discord_link={self.discord_link})>"

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

# Create table(s) if not present
Base.metadata.create_all(engine)