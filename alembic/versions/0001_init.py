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

    op.create_table(
        "contacts",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("company", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("email", name="uq_contacts_email"),
    )
    op.create_index("ix_contacts_email", "contacts", ["email"])

    op.create_table(
        "conversations",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("session_id", sa.String(length=100), nullable=False),
        sa.Column("contact_id", sa.Integer, sa.ForeignKey("contacts.id"), nullable=True),
        sa.Column("channel", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("session_id", name="uq_conversations_session_id"),
    )
    op.create_index("ix_conversations_session_id", "conversations", ["session_id"])
    op.create_index("ix_conversations_contact_id", "conversations", ["contact_id"])

    op.create_table(
        "messages",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("conversation_id", sa.Integer, sa.ForeignKey("conversations.id"), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"])

    op.create_table(
        "leads",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("contact_id", sa.Integer, sa.ForeignKey("contacts.id"), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("score", sa.Integer, nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_leads_contact_id", "leads", ["contact_id"])

    op.create_table(
        "tickets",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("contact_id", sa.Integer, sa.ForeignKey("contacts.id"), nullable=False),
        sa.Column("priority", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_tickets_contact_id", "tickets", ["contact_id"])

    op.create_table(
        "lead_events",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("lead_id", sa.Integer, sa.ForeignKey("leads.id"), nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("old_value", sa.String(length=255), nullable=True),
        sa.Column("new_value", sa.String(length=255), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("actor", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_lead_events_lead_id", "lead_events", ["lead_id"])

    op.create_table(
        "automation_drafts",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("kind", sa.String(length=50), nullable=False),
        sa.Column("lead_id", sa.Integer, sa.ForeignKey("leads.id"), nullable=True),
        sa.Column("ticket_id", sa.Integer, sa.ForeignKey("tickets.id"), nullable=True),
        sa.Column("contact_id", sa.Integer, sa.ForeignKey("contacts.id"), nullable=True),
        sa.Column("conversation_id", sa.Integer, sa.ForeignKey("conversations.id"), nullable=True),
        sa.Column("session_id", sa.String(length=128), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_automation_drafts_lead_id", "automation_drafts", ["lead_id"])
    op.create_index("ix_automation_drafts_ticket_id", "automation_drafts", ["ticket_id"])
    op.create_index("ix_automation_drafts_contact_id", "automation_drafts", ["contact_id"])
    op.create_index("ix_automation_drafts_conversation_id", "automation_drafts", ["conversation_id"])
    op.create_index("ix_automation_drafts_session_id", "automation_drafts", ["session_id"])

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

    op.create_table(
        "action_logs",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("lead_id", sa.Integer, sa.ForeignKey("leads.id"), nullable=True),
        sa.Column("ticket_id", sa.Integer, sa.ForeignKey("tickets.id"), nullable=True),
        sa.Column("action_type", sa.String(length=50), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_action_logs_lead_id", "action_logs", ["lead_id"])
    op.create_index("ix_action_logs_ticket_id", "action_logs", ["ticket_id"])

def downgrade():
    op.drop_index("ix_action_logs_ticket_id", table_name="action_logs")
    op.drop_index("ix_action_logs_lead_id", table_name="action_logs")
    op.drop_table("action_logs")

    op.drop_index("ix_automation_drafts_session_id", table_name="automation_drafts")
    op.drop_index("ix_automation_drafts_conversation_id", table_name="automation_drafts")
    op.drop_index("ix_automation_drafts_contact_id", table_name="automation_drafts")
    op.drop_index("ix_automation_drafts_ticket_id", table_name="automation_drafts")
    op.drop_index("ix_automation_drafts_lead_id", table_name="automation_drafts")
    op.drop_table("automation_drafts")

    op.drop_index("ix_lead_score_rules_active", table_name="lead_score_rules")
    op.drop_table("lead_score_rules")

    op.drop_index("ix_lead_events_lead_id", table_name="lead_events")
    op.drop_table("lead_events")

    op.drop_index("ix_tickets_contact_id", table_name="tickets")
    op.drop_table("tickets")

    op.drop_index("ix_leads_contact_id", table_name="leads")
    op.drop_table("leads")

    op.drop_index("ix_messages_conversation_id", table_name="messages")
    op.drop_table("messages")

    op.drop_index("ix_conversations_contact_id", table_name="conversations")
    op.drop_index("ix_conversations_session_id", table_name="conversations")
    op.drop_table("conversations")

    op.drop_index("ix_contacts_email", table_name="contacts")
    op.drop_table("contacts")

    op.drop_table("healthcheck")
