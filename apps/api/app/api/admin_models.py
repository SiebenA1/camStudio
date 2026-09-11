"""模型配置（管理后台）路由。"""
from __future__ import annotations

import time

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.ai import gateway
from app.ai.providers.base import ProviderConfig
from app.api.deps import get_current_user
from app.core.errors import AppError, ok
from app.core.security import decrypt_secret, encrypt_secret
from app.database import get_db
from app.models.model_config import ModelConfig
from app.models.tenant import User
from app.schemas.model_config import ModelConfigCreate, ModelConfigUpdate

router = APIRouter(prefix="/admin/models", tags=["model-config"])


def _mask(key: str) -> str:
    if not key:
        return ""
    if len(key) <= 8:
        return "****"
    return f"{key[:4]}****{key[-4:]}"


def _model_dict(m: ModelConfig) -> dict:
    return {
        "id": m.id,
        "tenant_id": m.tenant_id,
        "provider": m.provider,
        "name": m.name,
        "base_url": m.base_url,
        "api_key_masked": _mask(decrypt_secret(m.api_key)),
        "model": m.model,
        "task_type": m.task_type,
        "is_default": m.is_default,
        "enabled": m.enabled,
        "extra": m.extra,
    }


def _require_model_scope(user: User) -> None:
    if not (user.is_superuser or user.role == "admin"):
        raise AppError(403, "forbidden", "需要管理员权限")


@router.get("/providers")
def list_providers(user: User = Depends(get_current_user)):
    return ok(gateway.list_providers())


@router.get("")
def list_models(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    models = db.query(ModelConfig).filter(ModelConfig.tenant_id == user.tenant_id).order_by(
        ModelConfig.task_type, ModelConfig.is_default.desc()
    ).all()
    return ok([_model_dict(m) for m in models])


@router.post("")
def create_model(body: ModelConfigCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _require_model_scope(user)
    if body.is_default:
        _clear_default(db, user.tenant_id, body.task_type)
    m = ModelConfig(
        tenant_id=user.tenant_id, provider=body.provider, name=body.name,
        base_url=body.base_url, api_key=encrypt_secret(body.api_key), model=body.model,
        task_type=body.task_type, is_default=body.is_default, enabled=body.enabled,
        extra=body.extra,
    )
    db.add(m)
    db.commit()
    return ok(_model_dict(m))


@router.patch("/{model_id}")
def update_model(model_id: str, body: ModelConfigUpdate, db: Session = Depends(get_db),
                 user: User = Depends(get_current_user)):
    _require_model_scope(user)
    m = db.get(ModelConfig, model_id)
    if not m or m.tenant_id != user.tenant_id:
        raise AppError(404, "not_found", "模型配置不存在")
    data = body.model_dump(exclude_unset=True)
    if "api_key" in data:
        if data["api_key"]:
            m.api_key = encrypt_secret(data["api_key"])
        data.pop("api_key")
    for k, v in data.items():
        setattr(m, k, v)
    if m.is_default:
        _clear_default(db, user.tenant_id, m.task_type, except_id=m.id)
    db.commit()
    return ok(_model_dict(m))


@router.delete("/{model_id}")
def delete_model(model_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _require_model_scope(user)
    m = db.get(ModelConfig, model_id)
    if not m or m.tenant_id != user.tenant_id:
        raise AppError(404, "not_found", "模型配置不存在")
    db.delete(m)
    db.commit()
    return ok(None, "已删除")


@router.post("/{model_id}/test")
async def test_model(model_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    m = db.get(ModelConfig, model_id)
    if not m or m.tenant_id != user.tenant_id:
        raise AppError(404, "not_found", "模型配置不存在")
    key = decrypt_secret(m.api_key)
    if not key:
        return ok({"ok": False, "message": "尚未填写 API Key"})

    cfg = ProviderConfig(provider=m.provider, name=m.name, base_url=m.base_url,
                         api_key=key, model=m.model, task_type=m.task_type, extra=m.extra or {})
    start = time.time()
    try:
        provider = gateway.get_provider(m.provider)
        if m.task_type == "chat":
            await provider.chat(cfg, [{"role": "user", "content": "回复：OK"}], max_tokens=8)
        elif m.task_type == "vision":
            await provider.chat(cfg, [{"role": "user", "content": "回复：OK"}], max_tokens=8)
        elif m.task_type == "embed":
            await provider.embed(cfg, ["test"])
        elif m.task_type == "image":
            # 异步任务接口不做实际生成，仅校验配置可达
            return ok({"ok": True, "message": "配置有效（异步文生图，将在生成时验证）",
                       "latency_ms": int((time.time() - start) * 1000)})
        else:
            return ok({"ok": False, "message": f"暂不支持测试 task_type={m.task_type}"})
        return ok({"ok": True, "message": "连接成功", "latency_ms": int((time.time() - start) * 1000)})
    except Exception as e:
        return ok({"ok": False, "message": f"连接失败：{e}", "latency_ms": int((time.time() - start) * 1000)})


def _clear_default(db: Session, tenant_id: str, task_type: str, except_id: str | None = None) -> None:
    q = db.query(ModelConfig).filter(
        ModelConfig.tenant_id == tenant_id,
        ModelConfig.task_type == task_type,
        ModelConfig.is_default.is_(True),
    )
    if except_id:
        q = q.filter(ModelConfig.id != except_id)
    for m in q.all():
        m.is_default = False
