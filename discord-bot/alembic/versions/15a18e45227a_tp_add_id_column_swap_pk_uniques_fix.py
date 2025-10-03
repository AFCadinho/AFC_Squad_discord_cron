"""TP: add id column + swap PK + uniques (fix)

Revision ID: 15a18e45227a
Revises: 7ba5731d2f26
Create Date: 2025-10-02 08:40:04.081502
"""

from alembic import op
import sqlalchemy as sa

# ---- Alembic identifiers (must be plain assignments, no type hints) ----
revision = "15a18e45227a"
down_revision = "7ba5731d2f26"
branch_labels = None
depends_on = None
# ------------------------------------------------------------------------

TABLE = "tournament_participants"
SEQ   = "tournament_participants_id_seq"

def upgrade():
    # 1) add 'id' as a plain nullable integer
    op.add_column(TABLE, sa.Column("id", sa.Integer(), nullable=True))

    # 2) create a sequence and set it as the column default (Postgres-safe)
    op.execute(sa.text(f"CREATE SEQUENCE IF NOT EXISTS {SEQ}"))
    op.execute(sa.text(f"ALTER TABLE {TABLE} ALTER COLUMN id SET DEFAULT nextval('{SEQ}')"))
    op.execute(sa.text(f"ALTER SEQUENCE {SEQ} OWNED BY {TABLE}.id"))

    # 3) backfill existing rows using the DEFAULT
    op.execute(sa.text(f"UPDATE {TABLE} SET id = DEFAULT WHERE id IS NULL"))

    # 4) drop old composite PK (detect name dynamically)
    conn = op.get_bind()
    pk_name = conn.execute(sa.text(
        "SELECT conname FROM pg_constraint "
        f"WHERE conrelid = '{TABLE}'::regclass AND contype = 'p'"
    )).scalar()
    if pk_name:
        op.drop_constraint(pk_name, TABLE, type_="primary")

    # 5) set id NOT NULL and make it the primary key
    op.alter_column(TABLE, "id", nullable=False)
    op.create_primary_key(f"pk_{TABLE}", TABLE, ["id"])

    # 6) add uniques (comment out if already created in a previous migration)
    op.create_unique_constraint("uq_tp_tournament_user", TABLE, ["tournament_id", "user_id"])
    op.create_unique_constraint("uq_tp_tournament_chid", TABLE, ["tournament_id", "challonge_id"])

def downgrade():
    # drop uniques if present
    try:
        op.drop_constraint("uq_tp_tournament_chid", TABLE, type_="unique")
    except Exception:
        pass
    try:
        op.drop_constraint("uq_tp_tournament_user", TABLE, type_="unique")
    except Exception:
        pass

    # drop PK on id
    conn = op.get_bind()
    pk_name = conn.execute(sa.text(
        "SELECT conname FROM pg_constraint "
        f"WHERE conrelid = '{TABLE}'::regclass AND contype = 'p'"
    )).scalar()
    if pk_name:
        op.drop_constraint(pk_name, TABLE, type_="primary")

    # restore composite PK
    op.create_primary_key(f"{TABLE}_pkey", TABLE, ["tournament_id", "user_id"])

    # remove default + drop column + sequence
    op.execute(sa.text(f"ALTER TABLE {TABLE} ALTER COLUMN id DROP DEFAULT"))
    op.drop_column(TABLE, "id")
    op.execute(sa.text(f"DROP SEQUENCE IF EXISTS {SEQ}"))
