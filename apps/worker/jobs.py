from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from core.db import SessionLocal
from core.models.crm import Lead, Ticket, AutomationDraft, Conversation, Message
from core.llm.client import generate_llm_draft

DRAFT_DEDUP_WINDOW_MIN = 10

def _recent_pending_draft_exists(db: Session, *, kind: str, lead_id: int | None = None, ticket_id: int | None = None) -> bool:
    since = datetime.utcnow() - timedelta(minutes=DRAFT_DEDUP_WINDOW_MIN)
    q = db.query(AutomationDraft).filter(
        AutomationDraft.kind == kind,
        AutomationDraft.status == "pending",
        AutomationDraft.created_at >= since,   # relies on server_default func.now()
    )
    if lead_id is not None:
        q = q.filter(AutomationDraft.lead_id == lead_id)
    if ticket_id is not None:
        q = q.filter(AutomationDraft.ticket_id == ticket_id)
    return db.query(q.exists()).scalar()


def create_lead_followup_draft(lead_id: int):
    with SessionLocal() as db:
        lead = db.query(Lead).filter(Lead.id == lead_id).one_or_none()
        if lead is None:
            return {"ok": False, "error": "Lead not found", "lead_id": lead_id}

        if _recent_pending_draft_exists(db, kind="lead_followup", lead_id=lead.id):
            return {"ok": True, "skipped": True, "reason": "recent pending draft exists"}

        convo = (
            db.query(Conversation)
            .filter(Conversation.contact_id == lead.contact_id)
            .order_by(Conversation.id.desc())
            .first()
        )

        content = generate_llm_draft(lead_summary=lead.summary, context_docs=None)

        draft = AutomationDraft(
            kind="lead_followup",
            lead_id=lead.id,
            contact_id=lead.contact_id,
            conversation_id=convo.id if convo else None,
            session_id=convo.session_id if convo else None,
            status="pending",
            content=content,
        )
        db.add(draft)
        db.flush()  # ensures draft.id exists now

        if convo:
            db.add(
                Message(
                    conversation_id=convo.id,
                    role="system",
                    content=f"Draft created (pending):\n\n{content}",
                )
            )

        db.commit()
        return {"ok": True, "draft_id": draft.id}


def create_ticket_reply_draft(ticket_id: int):
    with SessionLocal() as db:
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).one_or_none()
        if ticket is None:
            return {"ok": False, "error": "Ticket not found", "ticket_id": ticket_id}

        if _recent_pending_draft_exists(db, kind="ticket_reply", ticket_id=ticket.id):
            return {"ok": True, "skipped": True, "reason": "recent pending draft exists"}

        convo = (
            db.query(Conversation)
            .filter(Conversation.contact_id == ticket.contact_id)
            .order_by(Conversation.id.desc())
            .first()
        )

        content = (
            "Hi there,\n\n"
            f"Thanks for reporting: “{ticket.summary}”.\n"
            "Can you confirm (1) device/browser, (2) exact error message, and (3) steps to reproduce?\n\n"
            "Best,\nClientOps AI Support"
        )

        draft = AutomationDraft(
            kind="ticket_reply",
            ticket_id=ticket.id,
            contact_id=ticket.contact_id,
            conversation_id=convo.id if convo else None,
            session_id=convo.session_id if convo else None,
            status="pending",
            content=content,
        )
        db.add(draft)
        db.flush()

        if convo:
            db.add(
                Message(
                    conversation_id=convo.id,
                    role="system",
                    content=f"Draft created (pending):\n\n{content}",
                )
            )

        db.commit()
        return {"ok": True, "draft_id": draft.id}
