"""Brief AI 拆解服务：文本 → 用户可指定的输入变量（人物 / 穿搭 / 场景）。

姿势 / 表情 / 构图属于「工具推导」的专业参数，由 reference_service 结合空镜场景
与 Brief 综合给出，不在本步骤要求用户指定。
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.ai import gateway
from app.core.jsonutil import extract_json_object
from app.core.variable_spec import INPUT_TYPES
from app.models.project import Brief, Variable

PARSE_SYSTEM = "你是资深商业摄影 Brief 解析助手，擅长把品牌需求拆解为可执行的视觉输入变量。"

PARSE_PROMPT = """请将下面的商业摄影 Brief 拆解为「用户可指定的输入变量」，只包含两类：character(人物)、outfit(穿搭/服装)。

重要：
- 场景(scene) 由空镜图本身决定，无需拆解，不要输出。
- 姿势(pose)、表情(expression)、构图(composition)、拍摄位置、角度 由工具根据真实空镜场景综合推导，**不需要用户指定**，不要输出它们。

对每一类变量：
- options: 从 Brief 中提取或合理推演的 2~5 个候选值（简短中文短语，不要整句）
- selected: 最符合 Brief 意图的 1 个值（数组，只有一个元素）
- weight: 该变量对整体视觉方向的重要程度，0~1 的小数

严格只输出 JSON，不要输出任何解释文字，格式如下：
{"character":{"options":["..."],"selected":["..."],"weight":0.9},"outfit":{"options":["..."],"selected":["..."],"weight":0.8}}

Brief 内容：
{text}"""


async def parse_brief_to_variables(db: Session, tenant_id: str, brief: Brief) -> dict:
    """调用文本模型拆解 Brief，落库为「输入类」Variable（并清理旧的推导类变量）。"""
    prompt = PARSE_PROMPT.replace("{text}", brief.raw_text)
    raw = await gateway.chat(
        db,
        tenant_id,
        [{"role": "system", "content": PARSE_SYSTEM}, {"role": "user", "content": prompt}],
        json_mode=True,
        temperature=0.2,
    )
    data = extract_json_object(raw)

    # 只保留三类输入变量
    data = {t: data.get(t, {"options": [], "selected": [], "weight": 0.5}) for t in INPUT_TYPES}

    brief.parsed_json = data
    brief.status = "parsed"
    db.add(brief)

    # 重建变量（旧的全部删除，含此前的推导类变量）
    project_id = brief.project_id
    db.query(Variable).filter(Variable.project_id == project_id).delete()
    for idx, t in enumerate(INPUT_TYPES):
        v = data[t]
        db.add(
            Variable(
                project_id=project_id,
                type=t,
                options=v.get("options", []),
                selected=v.get("selected", []),
                weight=float(v.get("weight", 0.5) or 0.5),
                sort=idx,
            )
        )
    db.commit()
    return data
