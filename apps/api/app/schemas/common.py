"""公共 schema。"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    """从 ORM 对象读取属性的公共配置。"""

    model_config = ConfigDict(from_attributes=True)
