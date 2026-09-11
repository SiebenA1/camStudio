"""拍摄设备（相机/镜头）官方参数获取与缓存。"""
from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.ai import gateway
from app.core.jsonutil import extract_json_object
from app.models.equipment import EquipmentProfile

EQUIPMENT_SYSTEM = "你是专业摄影器材顾问，熟悉各品牌相机与镜头的官方技术参数。"

EQUIPMENT_PROMPT = """请给出以下相机与镜头的官方技术参数（用于拍摄参数推荐）。若该型号信息不完整，请给出该类型设备的通用真实参数，并在 note 中标注「部分为通用值」。

相机：{camera}
镜头：{lens}

严格输出 JSON（不要其他文字）：
{
  "camera": {"model": "型号", "sensor": "传感器（全画幅/APS-C/M43）", "resolution": "像素", "iso_range": "ISO 范围", "shutter_range": "快门速度范围", "sync_speed": "闪光同步速度"},
  "lens": {"model": "型号", "focal_range": "焦段范围", "max_aperture": "最大光圈", "stabilization": "是否带防抖"},
  "note": "说明"
}"""


def get_or_create_profile(db: Session, tenant_id: str) -> EquipmentProfile:
    p = (
        db.query(EquipmentProfile)
        .filter(EquipmentProfile.tenant_id == tenant_id)
        .first()
    )
    if not p:
        p = EquipmentProfile(tenant_id=tenant_id)
        db.add(p)
        db.commit()
        db.refresh(p)
    return p


async def fetch_specs(db: Session, tenant_id: str, camera: str, lens: str) -> dict:
    """调用文本模型获取相机/镜头官方参数，并缓存到设备配置。"""
    prompt = (
        EQUIPMENT_PROMPT.replace("{camera}", camera or "（未填写）")
        .replace("{lens}", lens or "（未填写）")
    )
    raw = await gateway.chat(
        db,
        tenant_id,
        [{"role": "system", "content": EQUIPMENT_SYSTEM}, {"role": "user", "content": prompt}],
        json_mode=True,
        temperature=0.2,
    )
    data = extract_json_object(raw)
    p = get_or_create_profile(db, tenant_id)
    p.camera_model = camera
    p.lens_model = lens
    p.specs_json = data
    db.commit()
    return data


def equipment_text(profile: EquipmentProfile) -> str:
    """把设备信息渲染成给推荐模型的文本。"""
    if profile.specs_json:
        return json.dumps(profile.specs_json, ensure_ascii=False)
    cam = profile.camera_model or "未填写"
    lens = profile.lens_model or "未填写"
    return f"相机：{cam}；镜头：{lens}（暂无官方参数，请按通用全画幅设备推荐并说明）"
