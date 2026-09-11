"""预演生成路由。"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.projects import _get_project
from app.core.errors import AppError, ok
from app.core.storage import delete_local_file
from app.database import get_db
from app.models.previz import GenerationTask, PrevizAsset
from app.models.tenant import User
from app.schemas.previz import GenerateRequest, ScoreRequest
from app.services.previz_service import create_previz_generation
from app.services.score_service import score_asset

router = APIRouter(tags=["previz"])


def _asset_dict(a: PrevizAsset) -> dict:
    return {
        "id": a.id,
        "project_id": a.project_id,
        "combo_id": a.combo_id,
        "model": a.model,
        "provider": a.provider,
        "prompt": a.prompt,
        "prompt_hash": a.prompt_hash,
        "seed": a.seed,
        "params": a.params,
        "file_url": a.file_url,
        "thumbnail_url": a.thumbnail_url,
        "video_url": a.video_url,
        "status": a.status,
        "quality_score": a.quality_score,
        "quality_detail": a.quality_detail,
        "cost": a.cost,
        "version": a.version,
        "ai_ratio": a.ai_ratio,
        "error": a.error,
        "created_at": a.created_at.isoformat() if a.created_at else None,
        "updated_at": a.updated_at.isoformat() if a.updated_at else None,
    }


@router.post("/projects/{project_id}/previz/generate")
def generate(project_id: str, body: GenerateRequest, db: Session = Depends(get_db),
             user: User = Depends(get_current_user)):
    project = _get_project(db, user, project_id)
    assets, model, provider = create_previz_generation(
        db, project=project, request=body, tenant_id=user.tenant_id
    )
    return ok({
        "assets": [_asset_dict(a) for a in assets],
        "model": model,
        "provider": provider,
        "message": f"已提交 {len(assets)} 个生成任务",
    })


@router.get("/projects/{project_id}/previz")
def list_previz(project_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _get_project(db, user, project_id)
    assets = (
        db.query(PrevizAsset)
        .filter(PrevizAsset.project_id == project_id)
        .order_by(PrevizAsset.created_at.desc())
        .all()
    )
    return ok([_asset_dict(a) for a in assets])


@router.get("/previz/{asset_id}")
def get_previz(asset_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    a = db.get(PrevizAsset, asset_id)
    if not a or a.tenant_id != user.tenant_id:
        raise AppError(404, "not_found", "资产不存在")
    return ok(_asset_dict(a))


@router.delete("/previz/{asset_id}")
def delete_previz(asset_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    a = db.get(PrevizAsset, asset_id)
    if not a or a.tenant_id != user.tenant_id:
        raise AppError(404, "not_found", "资产不存在")
    # 删除关联生成任务
    db.query(GenerationTask).filter(GenerationTask.asset_id == asset_id).delete()
    # 删除本地文件（尽力而为）
    delete_local_file(a.file_url)
    delete_local_file(a.thumbnail_url)
    db.delete(a)
    db.commit()
    return ok(None, "已删除")


@router.post("/previz/{asset_id}/score")
async def score(asset_id: str, body: ScoreRequest, db: Session = Depends(get_db),
                user: User = Depends(get_current_user)):
    a = db.get(PrevizAsset, asset_id)
    if not a or a.tenant_id != user.tenant_id:
        raise AppError(404, "not_found", "资产不存在")
    data = await score_asset(db, user.tenant_id, a, body.reference_image_url, body.brand_color)
    return ok(data)


@router.get("/tasks/{task_id}")
def get_task(task_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    t = db.get(GenerationTask, task_id)
    if not t or t.tenant_id != user.tenant_id:
        raise AppError(404, "not_found", "任务不存在")
    return ok({
        "id": t.id,
        "asset_id": t.asset_id,
        "task_type": t.task_type,
        "provider": t.provider,
        "model": t.model,
        "status": t.status,
        "error": t.error,
        "cost": t.cost,
        "created_at": t.created_at.isoformat() if t.created_at else None,
    })


@router.get("/projects/{project_id}/costs")
def project_costs(project_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _get_project(db, user, project_id)
    tasks = db.query(GenerationTask).filter(GenerationTask.project_id == project_id).all()
    total = sum(t.cost for t in tasks)
    by_model: dict[str, float] = {}
    for t in tasks:
        key = f"{t.provider}:{t.model}"
        by_model[key] = by_model.get(key, 0.0) + t.cost
    return ok({"total_cost": total, "by_model": by_model, "task_count": len(tasks)})
