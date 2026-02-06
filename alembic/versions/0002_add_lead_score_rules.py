"""add lead score rules

Revision ID: 0002_add_lead_score_rules
Revises: 0001_init
Create Date: 2026-02-05
"""

from alembic import op
import sqlalchemy as sa

revision = "0002_add_lead_score_rules"
down_revision = "0001_init"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "lead_score_rules",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("field", sa.String(length=50), nullable=False),
        sa.Column("operator", sa.String(length=20), nullable=False),
        sa.Column("value", sa.String(length=255), nullable=False),
        sa.Column("points", sa.Integer, nullable=False),
        sa.Column("active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_lead_score_rules_active", "lead_score_rules", ["active"])


def downgrade():
    op.drop_index("ix_lead_score_rules_active", table_name="lead_score_rules")
    op.drop_table("lead_score_rules")
