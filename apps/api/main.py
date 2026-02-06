from fastapi import FastAPI, Depends
from apps.api.routers import health, ingest, chat, crm, conversations, auth
from core.config import settings

from core.db import engine
from core import models
from apps.api.routers import admin
from core.db_wait import wait_for_db
from apps.api.routers import admin_leads
from apps.api.routers.auth import get_current_user

wait_for_db(engine)

app = FastAPI(title=settings.app_name)

app.include_router(health.router, tags=["health"])
app.include_router(auth.router)
app.include_router(ingest.router, prefix="/ingest", tags=["ingest"], dependencies=[Depends(get_current_user)])
app.include_router(chat.router, prefix="/chat", tags=["chat"], dependencies=[Depends(get_current_user)])
app.include_router(crm.router, prefix="/crm", tags=["crm"], dependencies=[Depends(get_current_user)])
app.include_router(conversations.router, prefix="/conversations", tags=["conversations"], dependencies=[Depends(get_current_user)])
app.include_router(admin.router, prefix="/admin", tags=["admin"], dependencies=[Depends(get_current_user)])
app.include_router(admin_leads.router, dependencies=[Depends(get_current_user)])
