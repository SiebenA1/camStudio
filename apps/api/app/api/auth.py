"""认证路由。"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.errors import AppError, ok
from app.core.security import create_access_token, hash_password, verify_password
from app.database import get_db
from app.models.tenant import Tenant, User
from app.schemas.auth import LoginRequest, RegisterRequest

router = APIRouter(prefix="/auth", tags=["auth"])


def _user_dict(u: User) -> dict:
    return {
        "id": u.id,
        "tenant_id": u.tenant_id,
        "email": u.email,
        "name": u.name,
        "role": u.role,
        "status": u.status,
        "is_superuser": u.is_superuser,
    }


def _token_for(u: User) -> dict:
    token = create_access_token(u.id, {"tenant_id": u.tenant_id})
    return {"access_token": token, "token_type": "bearer", "user": _user_dict(u)}


@router.post("/login")
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise AppError(401, "bad_credentials", "邮箱或密码错误")
    if user.status != "active":
        raise AppError(403, "disabled", "账号已被禁用")
    return ok(_token_for(user))


@router.post("/register")
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == body.email).first():
        raise AppError(409, "exists", "该邮箱已注册")
    tenant_name = body.tenant_name or "我的团队"
    slug = "t-" + str(abs(hash(tenant_name)) % 10_000_000)
    tenant = Tenant(name=tenant_name, slug=slug, plan="free", status="active")
    db.add(tenant)
    db.flush()
    user = User(
        tenant_id=tenant.id,
        email=body.email,
        name=body.name,
        password_hash=hash_password(body.password),
        role="admin",
        is_superuser=False,
        status="active",
    )
    db.add(user)
    db.commit()
    return ok(_token_for(user))


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return ok(_user_dict(user))
