from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from apps.api.utils.auth import create_access_token, hash_password, verify_password, decode_token
from core.db import get_db
from core.models.crm import User, Tenant

router = APIRouter(prefix="/auth", tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    tenant_name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == req.email).one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    tenant = Tenant(name=req.tenant_name)
    db.add(tenant)
    db.flush()

    try:
        password_hash = hash_password(req.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    user = User(
        email=req.email,
        password_hash=password_hash,
        role="admin",
        tenant_id=tenant.id,
    )
    db.add(user)
    db.commit()

    token = create_access_token(subject=req.email, tenant_id=tenant.id, role=user.role)
    return {"access_token": token, "token_type": "bearer"}


@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).one_or_none()
    try:
        ok = user and verify_password(req.password, user.password_hash)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not ok:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(subject=user.email, tenant_id=user.tenant_id, role=user.role)
    return {"access_token": token, "token_type": "bearer"}


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.email == payload.get("sub")).one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid user")

    return user
