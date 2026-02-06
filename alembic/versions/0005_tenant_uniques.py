"""tenant scoped uniques

Revision ID: 0005_tenant_uniques
Revises: 0004_auth_multitenant
Create Date: 2026-02-05
"""

from alembic import op
import sqlalchemy as sa

revision = "0005_tenant_uniques"
down_revision = "0004_auth_multitenant"
branch_labels = None
depends_on = None


def upgrade():
    # Drop global uniques if they exist
    with op.batch_alter_table("contacts") as batch:
        try:
            batch.drop_constraint("uq_contacts_email", type_="unique")
        except Exception:
            pass
    with op.batch_alter_table("conversations") as batch:
        try:
            batch.drop_constraint("uq_conversations_session_id", type_="unique")
        except Exception:
            pass

    op.create_index("uq_contacts_tenant_email", "contacts", ["tenant_id", "email"], unique=True)
    op.create_index("uq_conversations_tenant_session", "conversations", ["tenant_id", "session_id"], unique=True)


def downgrade():
    op.drop_index("uq_conversations_tenant_session", table_name="conversations")
    op.drop_index("uq_contacts_tenant_email", table_name="contacts")

    with op.batch_alter_table("conversations") as batch:
        batch.create_unique_constraint("uq_conversations_session_id", ["session_id"])
    with op.batch_alter_table("contacts") as batch:
        batch.create_unique_constraint("uq_contacts_email", ["email"])
