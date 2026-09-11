"""质量评分服务：用视觉模型对预演图打分（国内替代 CLIP 评分）。"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.ai import gateway
from app.core.errors import AppError
from app.core.jsonutil import extract_json_object
from app.models.previz import PrevizAsset

SCORE_PROMPT = """请对这张商业摄影预演图进行质量评分，输出严格 JSON（不要其他文字）：
{"clarity":<0-100 清晰度>,"composition":<0-100 构图>,"brand_color_match":<0-100 品牌色一致>,"style_match":<0-100 风格匹配>,"overall":<0-100 综合>,"comment":"<简短中文点评>"}"""


async def score_asset(
    db: Session,
    tenant_id: str,
    asset: PrevizAsset,
    reference_image_url: str | None = None,
    brand_color: str | None = None,
) -> dict:
    if not asset.file_url:
        raise AppError(400, "asset_not_ready", "资产尚未生成图片，无法评分")

    prompt = SCORE_PROMPT
    if brand_color:
        prompt += f"\n品牌主色参考：{brand_color}"

    image_urls = [asset.file_url]
    if reference_image_url:
        image_urls.append(reference_image_url)

    raw = await gateway.vision(
        db, tenant_id, prompt, image_urls, json_mode=True, temperature=0.2
    )
    data = extract_json_object(raw)

    overall = float(data.get("overall", 0))
    asset.quality_score = overall
    asset.quality_detail = data
    db.commit()
    return data
