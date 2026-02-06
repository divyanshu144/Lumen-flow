from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.db import get_db
from apps.api.routers.auth import get_current_user
from core.models.crm import User
from core.models.crm import Conversation, Message

router = APIRouter()

@router.get("/{session_id}")
def get_conversation(session_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    convo = (
        db.query(Conversation)
        .filter(Conversation.session_id == session_id, Conversation.tenant_id == user.tenant_id)
        .one_or_none()
    )
    if convo is None:
        return {"session_id": session_id, "conversation_id": None, "messages": []}

    msgs = (
        db.query(Message)
        .filter(Message.conversation_id == convo.id, Message.tenant_id == user.tenant_id)
        .order_by(Message.id.asc())
        .all()
    )

    return {
        "session_id": session_id,
        "conversation_id": convo.id,
        "messages": [{"role": m.role, "content": m.content} for m in msgs],
    }
