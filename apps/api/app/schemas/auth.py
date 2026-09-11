"""认证相关 schema。"""
from __future__ import annotations

from pydantic import BaseModel

from app.schemas.common import ORMModel


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    email: str
    name: str
    password: str
    tenant_name: str | None = None


class UserOut(ORMModel):
    id: str
    tenant_id: str
    email: str
    name: str
    role: str
    status: str
    is_superuser: bool


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
