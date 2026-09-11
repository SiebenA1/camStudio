"""空镜参考图路由：上传、场景分析、拍摄指导、图生预演。"""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.projects import _get_project
from app.core.errors import AppError, ok
from app.core.storage import delete_local_file, save_bytes
from app.database import get_db
from app.models.reference import ReferenceShot
from app.models.tenant import User
from app.services.previz_service import create_i2i_generation
from app.services.reference_service import (
    analyze_reference_shot,
    build_framework_prompt,
    generate_guidance,
    get_pose_variations,
)

router = APIRouter(tags=["reference-shots"])

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/bmp"}


def _shot_dict(s: ReferenceShot) -> dict:
    return {
        "id": s.id,
        "project_id": s.project_id,
        "file_url": s.file_url,
        "filename": s.filename,
        "analysis_json": s.analysis_json,
        "guidance_json": s.guidance_json,
        "status": s.status,
        "created_at": s.created_at.isoformat() if s.created_at else None,
    }


def _get_shot(db: Session, user: User, shot_id: str) -> ReferenceShot:
    s = db.get(ReferenceShot, shot_id)
    if not s:
        raise AppError(404, "not_found", "空镜参考图不存在")
    if s.tenant_id != user.tenant_id:
        raise AppError(403, "forbidden", "无权访问该参考图")
    return s


@router.post("/projects/{project_id}/reference-shots")
async def upload_reference_shot(project_id: str, file: UploadFile = File(...),
                                db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _get_project(db, user, project_id)
    content = await file.read()
    if file.content_type and file.content_type not in ALLOWED_IMAGE_TYPES:
        raise AppError(400, "bad_image", "仅支持 JPG/PNG/WebP/BMP 图片")
    url = save_bytes(content, "reference", file.content_type)
    shot = ReferenceShot(
        tenant_id=user.tenant_id, project_id=project_id,
        file_url=url, filename=file.filename, status="uploaded",
    )
    db.add(shot)
    db.commit()
    return ok(_shot_dict(shot))


@router.get("/projects/{project_id}/reference-shots")
def list_reference_shots(project_id: str, db: Session = Depends(get_db),
                         user: User = Depends(get_current_user)):
    _get_project(db, user, project_id)
    shots = (
        db.query(ReferenceShot)
        .filter(ReferenceShot.project_id == project_id)
        .order_by(ReferenceShot.created_at.desc())
        .all()
    )
    return ok([_shot_dict(s) for s in shots])


@router.post("/reference-shots/{shot_id}/analyze")
async def analyze(shot_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    shot = _get_shot(db, user, shot_id)
    data = await analyze_reference_shot(db, user.tenant_id, shot)
    return ok(data)


@router.post("/reference-shots/{shot_id}/guidance")
async def guidance(shot_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    shot = _get_shot(db, user, shot_id)
    from app.models.project import Brief
    brief = db.query(Brief).filter(Brief.project_id == shot.project_id).first()
    data = await generate_guidance(db, user.tenant_id, shot, brief.raw_text if brief else "")
    return ok(data)


@router.post("/reference-shots/{shot_id}/generate")
def generate(shot_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """以空镜图为参考，一次生成 3 张不同姿势的「拍摄框架示意图」（图生图）。"""
    shot = _get_shot(db, user, shot_id)
    from app.models.project import Project
    project = db.get(Project, shot.project_id)
    if not project:
        raise AppError(404, "not_found", "项目不存在")

    poses = get_pose_variations(shot)
    asset_ids: list[str] = []
    prompts: list[str] = []
    for pose in poses:
        prompt = build_framework_prompt(shot, pose)
        asset = create_i2i_generation(
            db, project=project, shot=shot, prompt=prompt, tenant_id=user.tenant_id
        )
        asset_ids.append(asset.id)
        prompts.append(prompt)
    return ok({
        "asset_ids": asset_ids,
        "poses": poses,
        "message": f"已提交 {len(asset_ids)} 张框架示意图生成任务，稍后刷新预演资产查看",
    })


@router.post("/reference-shots/{shot_id}/replace")
async def replace_reference_shot(shot_id: str, file: UploadFile = File(...),
                                 db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """更换空镜图：上传新图替换旧图，并重置分析/指导结果。"""
    shot = _get_shot(db, user, shot_id)
    content = await file.read()
    if file.content_type and file.content_type not in ALLOWED_IMAGE_TYPES:
        raise AppError(400, "bad_image", "仅支持 JPG/PNG/WebP/BMP 图片")
    delete_local_file(shot.file_url)
    shot.file_url = save_bytes(content, "reference", file.content_type)
    shot.filename = file.filename
    shot.analysis_json = None
    shot.guidance_json = None
    shot.status = "uploaded"
    db.commit()
    return ok(_shot_dict(shot))


@router.delete("/reference-shots/{shot_id}")
def delete_reference_shot(shot_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    shot = _get_shot(db, user, shot_id)
    delete_local_file(shot.file_url)
    db.delete(shot)
    db.commit()
    return ok(None, "已删除")
