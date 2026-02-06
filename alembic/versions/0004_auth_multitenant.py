"""auth and multi-tenant

Revision ID: 0004_auth_multitenant
Revises: 0003_add_ticket_classification
Create Date: 2026-02-05
"""

from alembic import op
import sqlalchemy as sa

revision = "0004_auth_multitenant"
down_revision = "0003_add_ticket_classification"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "tenants",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.Integer, sa.ForeignKey("tenants.id"), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False, server_default="agent"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_tenant_id", "users", ["tenant_id"])

    for table in [
        "contacts",
        "conversations",
        "messages",
        "leads",
        "tickets",
        "lead_events",
        "automation_drafts",
        "action_logs",
        "lead_score_rules",
    ]:
        op.add_column(table, sa.Column("tenant_id", sa.Integer, sa.ForeignKey("tenants.id"), nullable=True))
        op.create_index(f"ix_{table}_tenant_id", table, ["tenant_id"])


def downgrade():
    for table in [
        "lead_score_rules",
        "action_logs",
        "automation_drafts",
        "lead_events",
        "tickets",
        "leads",
        "messages",
        "conversations",
        "contacts",
    ]:
        op.drop_index(f"ix_{table}_tenant_id", table_name=table)
        op.drop_column(table, "tenant_id")

    op.drop_index("ix_users_tenant_id", table_name="users")
    op.drop_table("users")
    op.drop_table("tenants")
