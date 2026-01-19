"""init

Revision ID: 0001_init
Revises:
Create Date: 2026-01-12

"""

from alembic import op
import sqlalchemy as sa

revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "healthcheck",
        sa.Column("key", sa.String(length=50), primary_key=True),
        sa.Column("value", sa.String(length=200), nullable=False, server_default="ok"),
    )

def downgrade():
    op.drop_table("healthcheck")
