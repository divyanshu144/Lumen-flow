from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from sqlalchemy import and_

from core.db import get_db
from apps.api.routers.auth import get_current_user
from core.models.crm import User
from core.queue import get_queue
from core.models.crm import Conversation, Message, Contact, Lead, Ticket
from apps.api.utils.replies import build_reply
from apps.api.utils.support import classify_ticket
from core.llm.client import generate_llm_reply

router = APIRouter()

class ChatRequest(BaseModel):
    session_id: str | None = None
    message: str
    email: str | None = None
    source: str | None = None
    name: str | None = None
    company: str | None = None
    crm: str | None = None
    goal: str | None = None


@router.post("")
def chat(req: ChatRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    session_id = req.session_id or "demo-session"
    tenant_id = user.tenant_id

    # 1) get or create conversation
    convo = (
        db.query(Conversation)
        .filter(Conversation.session_id == session_id, Conversation.tenant_id == tenant_id)
        .one_or_none()
    )
    if convo is None:
        convo = Conversation(session_id=session_id, channel="web", tenant_id=tenant_id)
        db.add(convo)
        db.commit()
        db.refresh(convo)

    # 2) UPSERT CONTACT + LINK TO CONVERSATION  ✅  (THIS IS WHERE IT GOES)
    contact_id = None
    if req.email:
        email = req.email.strip().lower()
        contact = (
            db.query(Contact)
            .filter(Contact.email == email, Contact.tenant_id == tenant_id)
            .one_or_none()
        )
        if contact is None:
            contact = Contact(email=email, tenant_id=tenant_id)
            db.add(contact)
            db.commit()
            db.refresh(contact)

        convo.contact_id = contact.id
        db.commit()
        contact_id = contact.id

    # 3) store user message
    user_msg = Message(
        conversation_id=convo.id,
        tenant_id=tenant_id,
        role="user",
        content=req.message,
    )
    db.add(user_msg)
    db.commit()

    # 4) rule-based triage
    text = req.message.lower()
    intent = "general"
    if any(k in text for k in ["price", "pricing", "quote", "cost", "book", "demo", "buy", "service"]):
        intent = "lead"
    elif any(k in text for k in ["error", "bug", "issue", "not working", "problem", "help"]):
        intent = "ticket"
    if req.source == "lead_capture":
        intent = "lead"

    lead = None
    ticket = None

    # Only create CRM objects if we have a contact_id
    if contact_id:
        if intent == "lead":
            lead = Lead(
                tenant_id=tenant_id,
                contact_id=contact_id,
                status="new",
                score=50,
                summary=req.message,
            )
            db.add(lead)
            db.commit()
            db.refresh(lead)

            # enqueue background job (RQ worker)
            get_queue().enqueue("apps.worker.jobs.create_lead_followup_draft", lead.id)

        elif intent == "ticket":
            classification = classify_ticket(req.message)
            ticket = Ticket(
                tenant_id=tenant_id,
                contact_id=contact_id,
                priority="medium",
                status="open",
                category="general",
                tag=classification["tag"],
                sentiment=classification["sentiment"],
                urgency=classification["urgency"],
                summary=req.message,
            )
            db.add(ticket)
            db.commit()
            db.refresh(ticket)

            get_queue().enqueue("apps.worker.jobs.create_ticket_reply_draft", ticket.id)


    # 5) assistant response (LLM with fallback)
    if req.source == "helper":
        text_l = req.message.lower()
        if any(greet in text_l for greet in ["hi", "hello", "hey", "good morning", "good evening"]):
            answer = (
                "Hi there! We help teams with CRM setup, integrations, automation, and support workflows. "
                "What are you trying to improve right now?"
            )
        else:
            helper_prompt = (
                "You are a business-focused chatbot for a ClientOps company. "
                "You may also answer basic general questions that help users understand CRM, automation, integrations, "
                "and support workflows at a high level. Avoid unrelated topics. "
                "Keep replies concise (3-6 sentences) and ask exactly one clarifying question."
            )
            answer = generate_llm_reply(req.message, system_override=helper_prompt) or build_reply(req.message)
    else:
        answer = generate_llm_reply(req.message) or build_reply(req.message)
    assistant_msg = Message(
        conversation_id=convo.id,
        tenant_id=tenant_id,
        role="assistant",
        content=answer,
    )
    db.add(assistant_msg)
    db.commit()

    return {
        "session_id": session_id,
        "answer": answer,
        "citations": [],
        "triage": {"intent": intent, "confidence": 0.6 if intent != "general" else 0.3},
        "contact_id": contact_id,
    }
