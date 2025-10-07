"""Add Column for tier in Pokemon

Revision ID: 357d7312af9a
Revises: 44c5bd1d311a
Create Date: 2025-08-03 11:33:00.841844
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = "357d7312af9a"
down_revision: Union[str, Sequence[str], None] = "44c5bd1d311a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(bind, table: str) -> bool:
    return inspect(bind).has_table(table)


def _has_column(bind, table: str, column: str) -> bool:
    insp = inspect(bind)
    try:
        cols = {c["name"] for c in insp.get_columns(table)}
    except Exception:
        return False
    return column in cols


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()

    if not _has_table(bind, "pokemon"):
        # Table doesn't exist on this DB; nothing to do.
        return

    # Add tier if missing
    if not _has_column(bind, "pokemon", "tier"):
        op.add_column("pokemon", sa.Column("tier", sa.String(length=16), nullable=True))

    # Add always_stored if missing
    if not _has_column(bind, "pokemon", "always_stored"):
        op.add_column(
            "pokemon",
            sa.Column("always_stored", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        )
        # If you don't want a persistent server_default, you can drop it after backfilling:
        # op.alter_column("pokemon", "always_stored", server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()

    if not _has_table(bind, "pokemon"):
        return

    if _has_column(bind, "pokemon", "always_stored"):
        op.drop_column("pokemon", "always_stored")

    if _has_column(bind, "pokemon", "tier"):
        op.drop_column("pokemon", "tier")
