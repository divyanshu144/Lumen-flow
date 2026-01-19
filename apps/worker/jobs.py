from sqlalchemy.orm import Session
from datetime import datetime

from core.db import SessionLocal
from core.models.crm import Lead, Ticket, AutomationDraft, Conversation, Message

def create_lead_followup_draft(lead_id: int):
    db: Session = SessionLocal()
    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).one()

        # try to find a conversation for the same contact (optional)
        convo = (
            db.query(Conversation)
            .filter(Conversation.contact_id == lead.contact_id)
            .order_by(Conversation.id.desc())
            .first()
        )

        content = (
            "Hi there,\n\n"
            f"Thanks for reaching out about: “{lead.summary}”.\n"
            "Could you share your timeline and budget range? If helpful, we can book a quick 15-min call.\n\n"
            "Best,\nClientOps AI"
        )

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

        # (optional) also store a system message so it shows in your Conversation Viewer immediately
        if convo:
            db.add(
                Message(
                    conversation_id=convo.id,
                    role="system",
                    content=f"Draft created (pending):\n\n{content}",
                )
            )

        db.commit()
        return {"draft_id": draft.id}
    finally:
        db.close()


def create_ticket_reply_draft(ticket_id: int):
    db: Session = SessionLocal()
    try:
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).one()

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

        if convo:
            db.add(
                Message(
                    conversation_id=convo.id,
                    role="system",
                    content=f"Draft created (pending):\n\n{content}",
                )
            )

        db.commit()
        return {"draft_id": draft.id}
    finally:
        db.close()