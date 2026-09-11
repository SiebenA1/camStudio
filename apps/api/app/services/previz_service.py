"""预演生成编排服务：Prompt 构建 + 资产/任务创建。"""
from __future__ import annotations

import hashlib

from sqlalchemy.orm import Session

from app.ai import gateway
from app.models.project import Project, VariableCombo, PromptTemplate
from app.models.previz import GenerationTask, PrevizAsset, AssetStatus, GenerationStatus
from app.models.reference import ReferenceShot
from app.schemas.previz import GenerateRequest

DEFAULT_TEMPLATE = (
    "商业摄影视觉方案：人物为{character}，穿搭{outfit}。"
    "场景、拍摄位置、角度、姿势、表情与构图由你作为摄影指导专业设计。"
    "电影级布光，主体清晰，品牌高级感，专业广告摄影，超高清细节。"
)


def _val(combo: dict, key: str) -> str:
    v = combo.get(key, "")
    if isinstance(v, str):
        return v
    if isinstance(v, list) and v:
        return str(v[0])
    return str(v)


def build_prompt(combo: dict, template_text: str | None = None) -> str:
    if template_text:
        prompt = template_text
        for k, v in combo.items():
            prompt = prompt.replace("{{%s}}" % k, _val(combo, k))
        return prompt
    return DEFAULT_TEMPLATE.format(
        character=_val(combo, "character"),
        outfit=_val(combo, "outfit"),
    )


def _prompt_hash(prompt: str) -> str:
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


def create_previz_generation(
    db: Session,
    *,
    project: Project,
    request: GenerateRequest,
    tenant_id: str,
) -> tuple[list[PrevizAsset], str, str]:
    """创建预演资产 + 生成任务，返回 (assets, model, provider)。"""
    # 解析模型配置，确定实际使用的 model/provider
    cfg = gateway.resolve_config(
        db, tenant_id, "image", model=request.model, provider=request.provider
    )

    # 确定组合列表
    combos: list[dict] = []
    if request.combo_ids:
        for cid in request.combo_ids:
            combo = db.get(VariableCombo, cid)
            if combo:
                combos.append(combo.combo)
    if not combos:
        combos = [{}]  # 无组合时生成一张默认

    # 模板文本
    template_text = None
    if request.template_id:
        tpl = db.get(PromptTemplate, request.template_id)
        if tpl:
            template_text = tpl.template

    size = f"{request.width}*{request.height}"
    assets: list[PrevizAsset] = []

    for combo in combos:
        prompt = request.prompt or build_prompt(combo, template_text)
        for _ in range(request.count):
            asset = PrevizAsset(
                tenant_id=tenant_id,
                project_id=project.id,
                model=cfg.model,
                provider=cfg.provider,
                prompt=prompt,
                prompt_hash=_prompt_hash(prompt),
                seed=request.seed,
                params={"size": size, "n": 1, "seed": request.seed},
                status=AssetStatus.PENDING.value,
                version=1,
                ai_ratio=1.0,
            )
            db.add(asset)
            db.flush()
            db.add(
                GenerationTask(
                    tenant_id=tenant_id,
                    project_id=project.id,
                    asset_id=asset.id,
                    task_type="image",
                    provider=cfg.provider,
                    model=cfg.model,
                    params={"prompt": prompt, "size": size, "n": 1, "seed": request.seed},
                    status=GenerationStatus.QUEUED.value,
                )
            )
            assets.append(asset)

    db.commit()
    return assets, cfg.model, cfg.provider


def create_i2i_generation(
    db: Session,
    *,
    project: Project,
    shot: ReferenceShot,
    prompt: str,
    tenant_id: str,
    count: int = 1,
    seed: int | None = None,
    size: str = "2K",
) -> PrevizAsset:
    """以空镜参考图为条件生成合成预演图（图生图）。返回首个资产。"""
    cfg = gateway.resolve_config(db, tenant_id, "image")
    asset = PrevizAsset(
        tenant_id=tenant_id,
        project_id=project.id,
        model=cfg.model,
        provider=cfg.provider,
        prompt=prompt,
        prompt_hash=_prompt_hash(prompt),
        seed=seed,
        params={"size": size, "n": 1, "seed": seed, "ref_image_url": shot.file_url},
        status=AssetStatus.PENDING.value,
        version=1,
        # 有真实空镜图作为参考，AI 参与度标 0.7（实拍场景 + AI 合成主体）
        ai_ratio=0.7,
    )
    db.add(asset)
    db.flush()
    db.add(
        GenerationTask(
            tenant_id=tenant_id,
            project_id=project.id,
            asset_id=asset.id,
            task_type="image",
            provider=cfg.provider,
            model=cfg.model,
            params={"prompt": prompt, "size": size, "n": 1, "seed": seed, "ref_image_url": shot.file_url},
            status=GenerationStatus.QUEUED.value,
        )
    )
    db.commit()
    return asset
