from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from core.db import get_db
from core.models.crm import Lead, LeadEvent

router = APIRouter(prefix="/admin/leads", tags=["admin-leads"])


class LeadUpdateRequest(BaseModel):
    status: str | None = Field(default=None)
    score: int | None = Field(default=None, ge=0, le=100)


class LeadNoteRequest(BaseModel):
    note: str = Field(min_length=1, max_length=5000)
    actor: str = Field(default="admin")


@router.patch("/{lead_id}")
def update_lead(lead_id: int, req: LeadUpdateRequest, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).one_or_none()
    if lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")

    # status change event
    if req.status is not None and req.status != lead.status:
        db.add(
            LeadEvent(
                lead_id=lead.id,
                event_type="status_changed",
                old_value=lead.status,
                new_value=req.status,
                actor="admin",
            )
        )
        lead.status = req.status

    # score change event
    if req.score is not None and req.score != lead.score:
        db.add(
            LeadEvent(
                lead_id=lead.id,
                event_type="score_changed",
                old_value=str(lead.score),
                new_value=str(req.score),
                actor="admin",
            )
        )
        lead.score = req.score

    db.commit()
    db.refresh(lead)

    return {"id": lead.id, "status": lead.status, "score": lead.score}


@router.post("/{lead_id}/notes")
def add_lead_note(lead_id: int, req: LeadNoteRequest, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).one_or_none()
    if lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")

    event = LeadEvent(
        lead_id=lead.id,
        event_type="note_added",
        note=req.note,
        actor=req.actor,
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    return {"event_id": event.id, "lead_id": lead.id}


@router.get("/{lead_id}/timeline")
def lead_timeline(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).one_or_none()
    if lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")

    events = (
        db.query(LeadEvent)
        .filter(LeadEvent.lead_id == lead_id)
        .order_by(LeadEvent.created_at.asc())
        .all()
    )

    return [
        {
            "id": e.id,
            "event_type": e.event_type,
            "old_value": e.old_value,
            "new_value": e.new_value,
            "note": e.note,
            "actor": e.actor,
            "created_at": e.created_at.isoformat(),
        }
        for e in events
    ]