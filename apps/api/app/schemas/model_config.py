"""模型配置相关 schema。"""
from __future__ import annotations

from pydantic import BaseModel, Field


class ModelConfigCreate(BaseModel):
    provider: str
    name: str
    base_url: str
    api_key: str = ""
    model: str
    task_type: str  # chat | vision | image | video | embed
    is_default: bool = False
    enabled: bool = True
    extra: dict = Field(default_factory=dict)


class ModelConfigUpdate(BaseModel):
    provider: str | None = None
    name: str | None = None
    base_url: str | None = None
    api_key: str | None = None  # 留空表示不更新
    model: str | None = None
    task_type: str | None = None
    is_default: bool | None = None
    enabled: bool | None = None
    extra: dict | None = None


class ModelConfigOut(BaseModel):
    id: str
    tenant_id: str
    provider: str
    name: str
    base_url: str
    api_key_masked: str  # 脱敏
    model: str
    task_type: str
    is_default: bool
    enabled: bool
    extra: dict


class TestResult(BaseModel):
    ok: bool
    message: str
    latency_ms: int | None = None
