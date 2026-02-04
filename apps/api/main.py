from fastapi import FastAPI
from apps.api.routers import health, ingest, chat, crm, conversations
from core.config import settings

from core.db import engine
from core import models
from apps.api.routers import admin
from core.db_wait import wait_for_db
from apps.api.routers import admin_leads

wait_for_db(engine)

app = FastAPI(title=settings.app_name)

app.include_router(health.router, tags=["health"])
app.include_router(ingest.router, prefix="/ingest", tags=["ingest"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(crm.router, prefix="/crm", tags=["crm"])
app.include_router(conversations.router, prefix="/conversations", tags=["conversations"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])
app.include_router(admin_leads.router)
