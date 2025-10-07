from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = "b99403bebda0"
down_revision = "357d7312af9a"
branch_labels = None
depends_on = None

def _has_table(bind, table: str) -> bool:
    return inspect(bind).has_table(table)

def _has_column(bind, table: str, column: str) -> bool:
    insp = inspect(bind)
    try:
        cols = {c["name"] for c in insp.get_columns(table)}
    except Exception:
        return False
    return column in cols

def upgrade():
    bind = op.get_bind()
    if not _has_table(bind, "users"):
        # This DB doesn't have the users table; skip safely.
        return
    if not _has_column(bind, "users", "pvp_experience"):
        op.add_column(
            "users",
            sa.Column("pvp_experience", sa.String(length=16), server_default="novice", nullable=False),
        )
        # Optional: drop default after backfill
        # op.alter_column("users", "pvp_experience", server_default=None)

def downgrade():
    bind = op.get_bind()
    if _has_table(bind, "users") and _has_column(bind, "users", "pvp_experience"):
        op.drop_column("users", "pvp_experience")
