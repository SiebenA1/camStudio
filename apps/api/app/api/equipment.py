"""拍摄设备配置路由：相机/镜头型号（下拉选择）+ 官方参数获取（一次缓存）。"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.equipment_catalog import catalog
from app.core.errors import AppError, ok
from app.database import get_db
from app.models.tenant import User
from app.services.equipment_service import fetch_specs, get_or_create_profile

router = APIRouter(prefix="/admin/equipment", tags=["equipment"])


class EquipmentUpdate(BaseModel):
    camera_model: str | None = None
    lens_model: str | None = None


def _profile_dict(p) -> dict:
    return {
        "camera_model": p.camera_model,
        "lens_model": p.lens_model,
        "specs": p.specs_json,
        "updated_at": p.updated_at.isoformat() if p.updated_at else None,
    }


@router.get("/catalog")
def get_catalog():
    """返回可选的相机/镜头型号目录（按品牌分组）。"""
    return ok(catalog())


@router.get("")
def get_equipment(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    p = get_or_create_profile(db, user.tenant_id)
    return ok(_profile_dict(p))


@router.put("")
def set_equipment(body: EquipmentUpdate, db: Session = Depends(get_db),
                  user: User = Depends(get_current_user)):
    p = get_or_create_profile(db, user.tenant_id)
    changed = (
        (body.camera_model or "") != (p.camera_model or "")
        or (body.lens_model or "") != (p.lens_model or "")
    )
    p.camera_model = body.camera_model
    p.lens_model = body.lens_model
    if changed:
        # 型号变了，旧参数作废，需重新获取
        p.specs_json = None
    db.commit()
    return ok(_profile_dict(p))


@router.post("/fetch-specs")
async def fetch_equipment_specs(body: EquipmentUpdate | None = None,
                                db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """获取官方参数：若请求体带型号则先保存，再获取并缓存。"""
    p = get_or_create_profile(db, user.tenant_id)
    camera = (body.camera_model if body and body.camera_model else p.camera_model) or ""
    lens = (body.lens_model if body and body.lens_model else p.lens_model) or ""
    if not camera and not lens:
        raise AppError(400, "no_equipment", "请先选择相机与镜头型号")
    await fetch_specs(db, user.tenant_id, camera, lens)
    return ok(_profile_dict(p))
