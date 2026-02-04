from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from datetime import datetime
from core.models.crm import Lead, Ticket, Conversation, Message

from core.db import get_db
from core.models.crm import Lead, Ticket, Contact, AutomationDraft
from pydantic import BaseModel

router = APIRouter()

@router.get("/leads")
def list_leads(db: Session = Depends(get_db)):
    rows = db.query(Lead).order_by(Lead.id.desc()).limit(100).all()
    return [
        {
            "id": r.id,
            "contact_id": r.contact_id,
            "status": r.status,
            "score": r.score,
            "summary": r.summary,
        }
        for r in rows
    ]

@router.get("/tickets")
def list_tickets(db: Session = Depends(get_db)):
    rows = db.query(Ticket).order_by(Ticket.id.desc()).limit(100).all()
    return [
        {
            "id": r.id,
            "contact_id": r.contact_id,
            "status": r.status,
            "priority": r.priority,
            "category": r.category,
            "summary": r.summary,
        }
        for r in rows
    ]

@router.get("/contacts")
def list_contacts(db: Session = Depends(get_db)):
    rows = db.query(Contact).order_by(Contact.id.desc()).limit(100).all()
    return [{"id": c.id, "email": c.email, "name": c.name, "company": c.company} for c in rows]


AUTO_ADVANCE_ON_APPROVE = {
    "new": "contacted",
    "open": "contacted",  # optional
}

class DraftOut(BaseModel):
    id: int
    lead_id: int | None
    kind: str
    status: str
    created_at: str
    content: str

@router.get("/leads/{lead_id}/drafts")
def list_lead_drafts(lead_id: int, db: Session = Depends(get_db)):
    drafts = (
        db.query(AutomationDraft)
        .filter(AutomationDraft.lead_id == lead_id)
        .order_by(AutomationDraft.created_at.desc())
        .all()
    )
    return [
        {
            "id": d.id,
            "lead_id": d.lead_id,
            "kind": d.kind,
            "status": d.status,
            "created_at": d.created_at.isoformat(),
            "content": d.content,
        }
        for d in drafts
    ]


@router.get("/drafts")
def list_drafts(status: str = "pending", db: Session = Depends(get_db)):
    q = db.query(AutomationDraft).order_by(AutomationDraft.id.desc())
    if status:
        q = q.filter(AutomationDraft.status == status)
    drafts = q.limit(200).all()

    return [
        {
            "id": d.id,
            "kind": d.kind,
            "status": d.status,
            "lead_id": d.lead_id,
            "ticket_id": d.ticket_id,
            "contact_id": d.contact_id,
            "conversation_id": d.conversation_id,
            "session_id": d.session_id,
            "created_at": d.created_at.isoformat() if d.created_at else None,
            "approved_at": d.approved_at.isoformat() if d.approved_at else None,
            "content": d.content,
        }
        for d in drafts
    ]


@router.post("/drafts/{draft_id}/approve")
def approve_draft(draft_id: int, db: Session = Depends(get_db)):
    draft = db.query(AutomationDraft).filter(AutomationDraft.id == draft_id).one_or_none()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    if draft.status != "pending":
        raise HTTPException(status_code=400, detail=f"Draft is not pending (status={draft.status})")

    # mark approved
    draft.status = "approved"
    draft.approved_at = datetime.utcnow()

    # log "SENT" into conversation (simulation)
    if draft.conversation_id:
        convo = db.query(Conversation).filter(Conversation.id == draft.conversation_id).one()
        db.add(
            Message(
                conversation_id=convo.id,
                role="system",
                content=f"APPROVED + SENT:\n\n{draft.content}",
            )
        )

    # auto-advance entity
    if draft.lead_id:
        lead = db.query(Lead).filter(Lead.id == draft.lead_id).one()
        # auto-advance rule (keep it simple and deterministic)
        if lead.status in (None, "new"):
            lead.status = "contacted"

    if draft.ticket_id:
        ticket = db.query(Ticket).filter(Ticket.id == draft.ticket_id).one()
        # optional: auto-advance ticket
        if ticket.status in (None, "open"):
            ticket.status = "open"  # or "in_progress"

    db.commit()

    return {"ok": True, "draft_id": draft.id, "status": draft.status}
