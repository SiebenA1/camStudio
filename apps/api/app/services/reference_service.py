"""空镜参考图服务：场景分析（视觉）+ 拍摄指导与要素（文本）+ 图生图 Prompt 构建。"""
from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.ai import gateway
from app.core.errors import AppError
from app.core.jsonutil import extract_json_object
from app.models.reference import ReferenceShot

# ---- 场景分析（视觉模型）----
ANALYSIS_PROMPT = """你是资深商业摄影指导。请分析这张「空镜图」（尚未放置主体的空场景/空机位照片），输出严格 JSON（不要其他文字）：

{
  "scene_type": "场景类型（街景/室内/棚拍/自然户外/建筑/其他）",
  "lighting": {"direction": "主光方向（顺光/侧光/逆光/顶光/环境光）", "temperature": "色温（暖/冷/中性）", "intensity": "强度（强/中/弱）", "note": "光线说明"},
  "camera": {"angle": "机位角度（平视/俯视/仰视）", "height": "机位高度（低/中/高）", "lens_suggestion": "建议镜头焦段"},
  "space": {"subject_zone": "主体适合放置的画面区域", "free_area": "可用留白空间说明"},
  "composition": {"vanishing_point": "透视消失点方向", "rule": "建议构图法则（三分法/对称/引导线/留白）", "note": "构图说明"},
  "color": {"palette": ["主色1", "主色2"], "mood": "色彩氛围"},
  "props": ["画面中已有的元素/道具"],
  "challenge": "拍摄该场景需注意的问题（反光/逆光补偿/人流/阴影等）"
}"""

# ---- 拍摄指导 + 要素（文本模型）----
GUIDANCE_SYSTEM = "你是资深商业摄影指导，擅长结合真实场景与客户需求，专业推导出可执行的拍摄参数。"

GUIDANCE_PROMPT = """请结合「空镜图场景分析」「用户指定的输入变量」与「客户 Brief」，**由你作为摄影指导专业推导**出拍摄所需的拍摄位置、角度、姿势、表情、构图等参数，并给出拍摄指导。

注意：拍摄位置、角度、姿势、表情、构图都必须由你根据场景透视/光线/空间与输入变量综合推导，不要照抄用户输入。

严格输出 JSON（不要其他文字）：

{
  "camera_plan": {
    "subject_position": "【推导】主体应站在画面中的具体位置（结合空间/透视/三分线）",
    "camera_angle": "【推导】推荐机位角度与焦段（平视/俯视/仰视 + 镜头焦段）",
    "shooting_position": "【推导】相机拍摄位置与方向（结合光线方向与场景结构）"
  },
  "shot_list": [{"shot": "镜头名", "camera": "机位/镜头", "subject": "主体站位与动作", "lighting": "灯光布置", "note": "要点"}],
  "elements": {
    "character": "人物落实建议（在用户指定基础上细化）",
    "outfit": "服装落实建议（在用户指定基础上细化）",
    "pose": "【推导】主要姿势建议",
    "expression": "【推导】表情建议",
    "composition": "【推导】构图建议（结合场景透视）"
  },
  "pose_variations": ["【推导】3 个差异明显的姿势，用于生成草图，如站立/行走/倚靠/回眸/坐姿"],
  "lighting_setup": "整体灯光布置方案",
  "props_needed": ["需补充的道具"],
  "risk_tips": ["拍摄风险与规避提示"]
}

【空镜图场景分析】
{scene}

【用户指定的输入变量】
{inputs}

【客户 Brief】
{brief}"""


async def analyze_reference_shot(db: Session, tenant_id: str, shot: ReferenceShot) -> dict:
    """用视觉模型分析空镜图，返回并存储场景分析结果。"""
    raw = await gateway.vision(
        db, tenant_id, ANALYSIS_PROMPT, [shot.file_url], json_mode=True, temperature=0.2
    )
    data = extract_json_object(raw)
    shot.analysis_json = data
    shot.status = "analyzed"
    db.commit()
    return data


async def generate_guidance(
    db: Session, tenant_id: str, shot: ReferenceShot, brief_text: str
) -> dict:
    """结合场景分析 + 用户输入变量 + Brief，由工具推导姿势/表情/构图等拍摄参数。"""
    if not shot.analysis_json:
        raise AppError(400, "not_analyzed", "请先执行「场景分析」")

    from app.core.variable_spec import INPUT_TYPES
    from app.models.project import Variable

    vars_ = (
        db.query(Variable)
        .filter(Variable.project_id == shot.project_id, Variable.type.in_(INPUT_TYPES))
        .all()
    )
    inputs = {v.type: v.selected for v in vars_ if v.selected}
    inputs_text = json.dumps(inputs, ensure_ascii=False) if inputs else "（用户未指定输入变量）"

    scene = json.dumps(shot.analysis_json, ensure_ascii=False)
    prompt = (
        GUIDANCE_PROMPT.replace("{scene}", scene)
        .replace("{inputs}", inputs_text)
        .replace("{brief}", brief_text or "（无 Brief，请基于场景给出通用商业摄影方案）")
    )
    raw = await gateway.chat(
        db,
        tenant_id,
        [{"role": "system", "content": GUIDANCE_SYSTEM}, {"role": "user", "content": prompt}],
        json_mode=True,
        temperature=0.3,
    )
    data = extract_json_object(raw)
    shot.guidance_json = data
    shot.status = "guided"
    db.commit()
    return data


def get_pose_variations(shot: ReferenceShot) -> list[str]:
    """取 3 个不同姿势（来自指导的 pose_variations，缺省时回退）。"""
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
    # 去重并补足到 3 个
    seen: list[str] = []
    for p in poses:
        if p not in seen:
            seen.append(p)
    while len(seen) < 3:
        seen.append(["站立", "行走", "倚靠"][len(seen) % 3])
    return seen[:3]


def build_framework_prompt(shot: ReferenceShot, pose: str) -> str:
    """构建「拍摄预演草图」Prompt：手绘漫画/素描风格，单色线稿，人物细节保留，含拍摄位置/角度。"""
    g = shot.guidance_json or {}
    elements = g.get("elements") or {}
    character = elements.get("character") or ""
    outfit = elements.get("outfit") or ""
    composition = elements.get("composition") or ""
    props = g.get("props_needed") or []
    camera_plan = g.get("camera_plan") or {}
    subject_position = camera_plan.get("subject_position") or ""
    camera_angle = camera_plan.get("camera_angle") or ""

    char_hint = f"人物为{character}，" if character else ""
    outfit_hint = f"穿搭{outfit}，" if outfit else ""
    comp_hint = f"构图遵循：{composition}。" if composition else ""
    props_hint = f"可搭配道具：{'、'.join(props)}。" if props else ""
    pos_hint = f"主体站位（拍摄位置）：{subject_position}。" if subject_position else ""
    angle_hint = f"机位角度：{camera_angle}。" if camera_angle else ""

    return (
        f"把这张空镜场景图转化为「拍摄预演草图」（手绘漫画/素描风格）："
        f"整体为黑白单色线稿，不上色、不做写实渲染、不要照片质感。"
        f"背景用简洁线条勾勒主要结构：透视消失点、地面线、柱子/墙体等关键轮廓，作为取景框架。"
        f"人物以手绘漫画/素描方式绘制，{char_hint}{outfit_hint}姿势为：{pose}；"
        f"身体比例自然，肢体、服装褶皱、配饰、道具等细节清晰可辨，线条干净利落。"
        f"{pos_hint}{angle_hint}{props_hint}{comp_hint}"
        f"保留原机位与透视，画面干净、留白充足，便于拍摄对象据此调整站位与动作。"
    )
