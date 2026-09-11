"""预演相关 schema。"""
from __future__ import annotations

from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    """提交文生图（预演）生成任务。"""

    combo_ids: list[str] = Field(default_factory=list)
    template_id: str | None = None
    prompt: str | None = None  # 直接指定 prompt 时忽略模板
    model: str | None = None   # 覆盖默认模型
    provider: str | None = None
    params: dict = Field(default_factory=dict)  # 尺寸/比例/张数等
    seed: int | None = None
    count: int = Field(default=1, ge=1, le=8)
    width: int = Field(default=1024, ge=256, le=2048)
    height: int = Field(default=1024, ge=256, le=2048)


class ScoreRequest(BaseModel):
    reference_image_url: str | None = None
    brand_color: str | None = None


class VideoRequest(BaseModel):
    duration: int = Field(default=5, ge=3, le=10)
    prompt: str | None = None


class PrevizAssetOut(BaseModel):
    id: str
    project_id: str
    model: str
    provider: str
    prompt: str
    seed: int | None
    params: dict
    file_url: str | None
    thumbnail_url: str | None
    video_url: str | None
    status: str
    quality_score: float | None
    cost: float
    version: int
    ai_ratio: float
    error: str | None
    created_at: str
    updated_at: str
