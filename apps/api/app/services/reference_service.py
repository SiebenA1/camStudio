"""模特照片预演服务：照片分析（视觉）+ 拍摄建议与相机参数（文本）+ 草图 Prompt 构建。

新流程：上传一张带模特的实拍照片 → 视觉模型自动分析场景/背景/光线/人像/穿着/道具等
→ 结合拍摄设备参数（相机/镜头，已缓存）推导姿势/构图与推荐相机参数 → 生成手绘预演草图。
全程无需 Brief 或其它额外提示。
"""
from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.ai import gateway
from app.core.errors import AppError
from app.core.jsonutil import extract_json_object
from app.models.reference import ReferenceShot
from app.services.equipment_service import equipment_text, get_or_create_profile

# ---- 照片分析（视觉模型）----
ANALYSIS_PROMPT = """你是资深商业摄影指导。请分析这张「模特实拍照片」，提取影响出图的关键元素，输出严格 JSON（不要其他文字）：

{
  "scene": {"type": "场景类型（街景/室内/棚拍/自然户外/建筑/其他）", "background": "背景元素描述"},
  "lighting": {"direction": "主光方向（顺光/侧光/逆光/顶光/环境光）", "temperature": "色温（暖/冷/中性）", "intensity": "强度（强/中/弱）", "note": "光线说明"},
  "model": {"gender": "性别", "age": "年龄段", "style": "气质/风格", "pose": "当前姿势", "expression": "当前表情"},
  "outfit": {"clothing": "服装描述（款式/材质/颜色）", "accessories": ["配饰"], "colors": ["服装主色"]},
  "props": ["画面中的道具/元素"],
  "composition": {"rule": "构图法则（三分法/对称/引导线/留白）", "angle": "机位角度（平视/俯视/仰视）", "note": "构图说明"},
  "color": {"palette": ["主色1", "主色2"], "mood": "色彩氛围"},
  "improvement": ["当前照片可优化/可调整的点"]
}"""

# ---- 拍摄建议 + 相机参数（文本模型）----
RECOMMEND_SYSTEM = "你是资深商业摄影指导，擅长根据照片与设备参数给出专业的拍摄预演建议与相机参数。"

RECOMMEND_PROMPT = """请根据「模特照片分析」与「拍摄设备参数」，自动给出拍摄预演建议与推荐相机拍摄参数。无需用户任何额外输入。

每个相机参数请严格用「首选值；补充说明」格式：分号前只放**核心参数值**（尽量简短，便于快速阅读），分号后放条件说明。

严格输出 JSON（不要其他文字）：

{
  "camera_params": {
    "aperture": "首选光圈值；条件说明",
    "shutter_speed": "首选快门值；条件说明",
    "iso": "首选 ISO 值；条件说明",
    "focal_length": "首选焦段；条件说明",
    "white_balance": "白平衡设置；条件说明",
    "drive_mode": "驱动模式；条件说明",
    "note": "整体参数说明（为何这样设置，结合场景光线与设备）"
  },
  "elements": {
    "pose": "建议姿势",
    "expression": "建议表情",
    "composition": "建议构图"
  },
  "pose_variations": ["3 个不同姿势建议，差异明显，如站立/行走/倚靠/回眸/坐姿"],
  "risk_tips": ["拍摄风险与规避提示"]
}

【模特照片分析】
{analysis}

【拍摄设备参数】
{equipment}"""


async def analyze_reference_shot(db: Session, tenant_id: str, shot: ReferenceShot) -> dict:
    """用视觉模型分析模特照片，返回并存储分析结果。"""
    raw = await gateway.vision(
        db, tenant_id, ANALYSIS_PROMPT, [shot.file_url], json_mode=True, temperature=0.2
    )
    data = extract_json_object(raw)
    shot.analysis_json = data
    shot.status = "analyzed"
    db.commit()
    return data


async def generate_recommendation(db: Session, tenant_id: str, shot: ReferenceShot) -> dict:
    """结合照片分析 + 设备参数，推导拍摄建议与推荐相机参数（无需 Brief）。"""
    if not shot.analysis_json:
        raise AppError(400, "not_analyzed", "请先执行「照片分析」")

    profile = get_or_create_profile(db, tenant_id)
    analysis = json.dumps(shot.analysis_json, ensure_ascii=False)
    prompt = (
        RECOMMEND_PROMPT.replace("{analysis}", analysis)
        .replace("{equipment}", equipment_text(profile))
    )
    raw = await gateway.chat(
        db,
        tenant_id,
        [{"role": "system", "content": RECOMMEND_SYSTEM}, {"role": "user", "content": prompt}],
        json_mode=True,
        temperature=0.3,
    )
    data = extract_json_object(raw)
    shot.guidance_json = data
    shot.status = "recommended"
    db.commit()
    return data


def get_pose_variations(shot: ReferenceShot) -> list[str]:
    """取 3 个不同姿势（来自建议的 pose_variations，缺省时回退）。"""
    g = shot.guidance_json or {}
    poses = g.get("pose_variations")
    if isinstance(poses, list):
        poses = [p for p in poses if isinstance(p, str) and p.strip()]
    if not poses:
        base = (g.get("elements") or {}).get("pose")
        if isinstance(base, str) and base.strip():
            poses = [base, f"{base}（变换角度）", f"{base}（变换动作）"]
        else:
            poses = ["站立正面", "侧身倚靠", "行走回眸"]
    seen: list[str] = []
    for p in poses:
        if p not in seen:
            seen.append(p)
    while len(seen) < 3:
        seen.append(["站立", "行走", "倚靠"][len(seen) % 3])
    return seen[:3]


# ---- 渲染程度（细节级别）----
RENDER_LEVELS: dict[str, dict] = {
    "outline": {
        "label": "轮廓",
        "detail": "只勾勒背景主要结构轮廓线与人物姿势轮廓（剪影/极简线条），不要五官、不要服装褶皱、不要道具细节，纯线条轮廓即可",
    },
    "simple": {
        "label": "简笔",
        "detail": "用简洁线条勾勒背景结构与人物肢体、服装的基本轮廓，脸部简单卡通化，保留少量细节",
    },
    "detailed": {
        "label": "精细",
        "detail": "保留服装褶皱、配饰、道具等细节，脸部以卡通形象绘制，线条干净利落",
    },
}


def build_framework_prompt(
    shot: ReferenceShot, pose: str, style_hint: str = "", render_level: str = "detailed"
) -> str:
    """构建「拍摄预演草图」Prompt：卡通风格（不复刻真人脸），渲染程度可调。"""
    g = shot.guidance_json or {}
    analysis = shot.analysis_json or {}
    elements = g.get("elements") or {}
    model = analysis.get("model") or {}
    outfit = analysis.get("outfit") or {}
    composition = elements.get("composition") or (analysis.get("composition") or {}).get("note") or ""
    props = analysis.get("props") or []

    gender = model.get("gender") or ""
    model_style = model.get("style") or ""
    outfit_hint = outfit.get("clothing") or ""
    comp_hint = f"构图遵循：{composition}。" if composition else ""
    style_line = f"整体姿势风格：{style_hint}。" if style_hint else ""

    level = RENDER_LEVELS.get(render_level, RENDER_LEVELS["detailed"])
    detail = level["detail"]

    if render_level == "outline":
        # 最低渲染：只轮廓，无脸无服装无道具细节
        face_line = ""
        outfit_props_line = ""
    else:
        face_desc = "、".join([p for p in [gender, model_style] if p])
        face_line = (
            f"人物不要复刻照片中模特的真实五官与相貌，脸部以{face_desc}对应的卡通形象绘制。"
            if face_desc
            else "人物不要复刻真人五官与相貌，脸部用通用卡通形象。"
        )
        outfit_props_line = ""
        if outfit_hint:
            outfit_props_line += f"穿着：{outfit_hint}。"
        if props:
            outfit_props_line += f"道具：{'、'.join(props)}。"

    return (
        f"把这张模特实拍照片转化为「拍摄预演草图」（手绘漫画/卡通风格）："
        f"整体为黑白单色线稿，不上色、不做写实渲染、不要照片质感。"
        f"保留照片中的场景结构、光线氛围。"
        f"{face_line}"
        f"人物姿势改为：{pose}。"
        f"{outfit_props_line}"
        f"{detail}。"
        f"{style_line}{comp_hint}"
        f"画面干净、留白充足。"
    )
