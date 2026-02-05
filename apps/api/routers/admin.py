from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from datetime import datetime
from core.models.crm import Lead, Ticket, Conversation, Message

from core.db import get_db
from core.models.crm import Lead, Ticket, Contact, AutomationDraft, Conversation, Message, LeadScoreRule, LeadEvent
from pydantic import BaseModel

router = APIRouter()


def _classify_intent(text: str) -> str:
    text_l = (text or "").lower()
    if any(k in text_l for k in ["price", "pricing", "quote", "cost", "book", "demo", "buy", "service"]):
        return "lead"
    if any(k in text_l for k in ["error", "bug", "issue", "not working", "problem", "help"]):
        return "ticket"
    return "general"


def _apply_rule(lead: Lead, rule: LeadScoreRule) -> int:
    field_value = ""
    if rule.field == "summary":
        field_value = (lead.summary or "").lower()
    elif rule.field == "status":
        field_value = (lead.status or "").lower()

    rule_value = (rule.value or "").lower()
    if rule.operator == "contains" and rule_value in field_value:
        return rule.points
    if rule.operator == "equals" and rule_value == field_value:
        return rule.points
    return 0


@router.get("/metrics")
def get_metrics(db: Session = Depends(get_db)):
    contacts = db.query(Contact).count()
    leads = db.query(Lead).count()
    tickets = db.query(Ticket).count()
    conversations = db.query(Conversation).count()
    messages = db.query(Message).count()
    drafts_total = db.query(AutomationDraft).count()
    drafts_pending = db.query(AutomationDraft).filter(AutomationDraft.status == "pending").count()
    drafts_approved = db.query(AutomationDraft).filter(AutomationDraft.status == "approved").count()

    # Avg response time: first assistant reply after first user msg per conversation
    avg_response_sec = None
    convo_ids = [c.id for c in db.query(Conversation.id).all()]
    deltas = []
    for cid in convo_ids:
        msgs = (
            db.query(Message)
            .filter(Message.conversation_id == cid)
            .order_by(Message.id.asc())
            .all()
        )
        first_user = next((m for m in msgs if m.role == "user"), None)
        if not first_user:
            continue
        first_assistant = next((m for m in msgs if m.role == "assistant" and m.id > first_user.id), None)
        if not first_assistant:
            continue
        deltas.append((first_assistant.created_at - first_user.created_at).total_seconds())

    if deltas:
        avg_response_sec = sum(deltas) / len(deltas)

    return {
        "contacts": contacts,
        "leads": leads,
        "tickets": tickets,
        "conversations": conversations,
        "messages": messages,
        "drafts_total": drafts_total,
        "drafts_pending": drafts_pending,
        "drafts_approved": drafts_approved,
        "avg_response_sec": avg_response_sec,
    }


@router.get("/intent")
def get_intent_distribution(db: Session = Depends(get_db), limit: int = 200):
    rows = (
        db.query(Message)
        .filter(Message.role == "user")
        .order_by(Message.id.desc())
        .limit(limit)
        .all()
    )
    counts = {"lead": 0, "ticket": 0, "general": 0}
    for m in rows:
        counts[_classify_intent(m.content)] += 1
    return counts


@router.post("/seed-demo")
def seed_demo(db: Session = Depends(get_db)):
    # Minimal demo dataset
    c1 = Contact(email="aanya@ridge.io", name="Aanya Rao", company="Ridge Logistics")
    c2 = Contact(email="sam@coastlabs.com", name="Sam Patel", company="Coast Labs")
    db.add_all([c1, c2])
    db.flush()

    conv1 = Conversation(session_id="demo-session", channel="web", contact_id=c1.id)
    conv2 = Conversation(session_id="support-session", channel="web", contact_id=c2.id)
    db.add_all([conv1, conv2])
    db.flush()

    m1 = Message(conversation_id=conv1.id, role="user", content="We need HubSpot + WhatsApp integration.")
    m2 = Message(conversation_id=conv1.id, role="assistant", content="Got it. Which CRM team owns routing today?")
    m3 = Message(conversation_id=conv2.id, role="user", content="Login error on mobile app, getting 500.")
    m4 = Message(conversation_id=conv2.id, role="assistant", content="Thanks. Can you share device + exact error?")
    db.add_all([m1, m2, m3, m4])

    lead = Lead(contact_id=c1.id, status="new", score=62, summary=m1.content)
    ticket = Ticket(contact_id=c2.id, status="open", priority="high", category="auth", summary=m3.content)
    db.add_all([lead, ticket])
    db.flush()

    draft = AutomationDraft(
        kind="lead_followup",
        lead_id=lead.id,
        contact_id=c1.id,
        conversation_id=conv1.id,
        session_id=conv1.session_id,
        status="pending",
        content="Hi Aanya, thanks for reaching out. Want to schedule a quick 15‑minute call to align on routing and data fields?",
    )
    db.add(draft)
    db.commit()

    return {"ok": True, "seeded": True}


@router.get("/score/rules")
def list_score_rules(db: Session = Depends(get_db)):
    rows = db.query(LeadScoreRule).order_by(LeadScoreRule.id.desc()).all()
    return [
        {
            "id": r.id,
            "name": r.name,
            "field": r.field,
            "operator": r.operator,
            "value": r.value,
            "points": r.points,
            "active": r.active,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]


@router.post("/score/rules")
def create_score_rule(payload: dict, db: Session = Depends(get_db)):
    required = ["name", "field", "operator", "value", "points"]
    if any(k not in payload for k in required):
        raise HTTPException(status_code=400, detail="Missing required fields")

    rule = LeadScoreRule(
        name=str(payload["name"]),
        field=str(payload["field"]),
        operator=str(payload["operator"]),
        value=str(payload["value"]),
        points=int(payload["points"]),
        active=bool(payload.get("active", True)),
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return {"ok": True, "id": rule.id}


@router.patch("/score/rules/{rule_id}")
def update_score_rule(rule_id: int, payload: dict, db: Session = Depends(get_db)):
    rule = db.query(LeadScoreRule).filter(LeadScoreRule.id == rule_id).one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    for field in ["name", "field", "operator", "value", "points", "active"]:
        if field in payload:
            setattr(rule, field, payload[field])

    db.commit()
    return {"ok": True, "id": rule.id}


@router.delete("/score/rules/{rule_id}")
def delete_score_rule(rule_id: int, db: Session = Depends(get_db)):
    rule = db.query(LeadScoreRule).filter(LeadScoreRule.id == rule_id).one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    db.delete(rule)
    db.commit()
    return {"ok": True, "id": rule_id}


@router.post("/score/recompute")
def recompute_scores(db: Session = Depends(get_db)):
    rules = db.query(LeadScoreRule).filter(LeadScoreRule.active == True).all()
    leads = db.query(Lead).all()
    updated = 0
    for lead in leads:
        old = lead.score or 0
        new_score = sum(_apply_rule(lead, r) for r in rules)
        if new_score != old:
            lead.score = new_score
            db.add(
                LeadEvent(
                    lead_id=lead.id,
                    event_type="score_recomputed",
                    old_value=str(old),
                    new_value=str(new_score),
                    actor="system",
                )
            )
            updated += 1
    db.commit()
    return {"ok": True, "updated": updated, "rules": len(rules)}


@router.get("/sla")
def get_sla(db: Session = Depends(get_db), threshold_sec: int = 300, limit: int = 50):
    conversations = (
        db.query(Conversation)
        .order_by(Conversation.id.desc())
        .limit(limit)
        .all()
    )
    rows = []
    for convo in conversations:
        msgs = (
            db.query(Message)
            .filter(Message.conversation_id == convo.id)
            .order_by(Message.id.asc())
            .all()
        )
        first_user = next((m for m in msgs if m.role == "user"), None)
        first_assistant = next(
            (m for m in msgs if m.role == "assistant" and first_user and m.id > first_user.id), None
        )
        if not first_user or not first_assistant:
            continue
        response_sec = (first_assistant.created_at - first_user.created_at).total_seconds()
        rows.append(
            {
                "session_id": convo.session_id,
                "contact_id": convo.contact_id,
                "response_sec": response_sec,
                "status": "met" if response_sec <= threshold_sec else "breached",
                "first_user_at": first_user.created_at.isoformat(),
                "first_assistant_at": first_assistant.created_at.isoformat(),
            }
        )
    return rows

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


@router.post("/drafts/{draft_id}/reject")
def reject_draft(draft_id: int, db: Session = Depends(get_db)):
    draft = db.query(AutomationDraft).filter(AutomationDraft.id == draft_id).one_or_none()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    if draft.status != "pending":
        raise HTTPException(status_code=400, detail=f"Draft is not pending (status={draft.status})")

    draft.status = "rejected"
    db.commit()
    return {"ok": True, "draft_id": draft.id, "status": draft.status}


@router.patch("/drafts/{draft_id}")
def update_draft(draft_id: int, payload: dict, db: Session = Depends(get_db)):
    draft = db.query(AutomationDraft).filter(AutomationDraft.id == draft_id).one_or_none()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    if draft.status != "pending":
        raise HTTPException(status_code=400, detail=f"Draft is not pending (status={draft.status})")

    content = payload.get("content")
    if not content or not isinstance(content, str):
        raise HTTPException(status_code=400, detail="content is required")

    draft.content = content
    db.commit()
    db.refresh(draft)
    return {"ok": True, "draft_id": draft.id, "status": draft.status, "content": draft.content}
