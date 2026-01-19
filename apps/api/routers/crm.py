from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class ContactUpsert(BaseModel):
    email: str
    name: str | None = None
    company: str | None = None
    notes: str | None = None

@router.post("/contacts/upsert")
def upsert_contact(payload: ContactUpsert):
    # Day 6: integrate HubSpot OR internal CRM tables
    return {"status": "queued", "payload": payload.model_dump(), "next": "Day 6: persist + integrate"}
