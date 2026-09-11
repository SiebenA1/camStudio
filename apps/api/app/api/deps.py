"""FastAPI 依赖：DB 会话、当前用户、权限。"""
from __future__ import annotations

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.security import decode_access_token
from app.database import get_db
from app.models.tenant import User

_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    if not creds:
        raise AppError(401, "unauthorized", "未登录")
    try:
        payload = decode_access_token(creds.credentials)
    except Exception:
        raise AppError(401, "unauthorized", "登录已过期，请重新登录")
    user_id = payload.get("sub")
    user = db.get(User, user_id)
    if not user or user.status != "active":
        raise AppError(401, "unauthorized", "用户不存在或已禁用")
    return user


def get_current_superuser(user: User = Depends(get_current_user)) -> User:
    if not user.is_superuser:
        raise AppError(403, "forbidden", "需要管理员权限")
    return user
