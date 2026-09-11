"""变量语义规范。

- INPUT_TYPES：用户指定的创作输入（人物 / 服装）—— 用户选择或自行输入。
  场景不再作为输入：场景就是空镜图本身，由工具从空镜图中分析。
- DERIVED_TYPES：工具推导的专业参数（姿势 / 表情 / 构图 / 拍摄位置 / 角度）——
  由工具结合空镜场景分析综合给出，不要求用户指定。
"""
from __future__ import annotations

INPUT_TYPES: list[str] = ["character", "outfit"]
DERIVED_TYPES: list[str] = ["pose", "expression", "composition", "position", "angle"]

TYPE_LABELS: dict[str, str] = {
    "character": "人物",
    "outfit": "穿搭 / 服装",
    "pose": "姿势",
    "expression": "表情",
    "composition": "构图",
    "position": "拍摄位置",
    "angle": "拍摄角度",
}
