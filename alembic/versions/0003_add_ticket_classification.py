"""add ticket classification

Revision ID: 0003_add_ticket_classification
Revises: 0002_add_lead_score_rules
Create Date: 2026-02-05
"""

from alembic import op
import sqlalchemy as sa

revision = "0003_add_ticket_classification"
down_revision = "0002_add_lead_score_rules"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("tickets", sa.Column("tag", sa.String(length=50), nullable=True))
    op.add_column("tickets", sa.Column("sentiment", sa.String(length=20), nullable=True))
    op.add_column("tickets", sa.Column("urgency", sa.String(length=20), nullable=True))


def downgrade():
    op.drop_column("tickets", "urgency")
    op.drop_column("tickets", "sentiment")
    op.drop_column("tickets", "tag")
