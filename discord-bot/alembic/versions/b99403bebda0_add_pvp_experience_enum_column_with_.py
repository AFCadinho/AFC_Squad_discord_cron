from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "b99403bebda0"
down_revision = "357d7312af9a"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column(
        "users",
        sa.Column("pvp_experience", sa.String(length=16), server_default="novice", nullable=False),
    )

def downgrade():
    op.drop_column("users", "pvp_experience")
