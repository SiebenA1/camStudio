"""预演资产与生成任务模型。"""
from __future__ import annotations

import enum

from sqlalchemy import JSON, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import (
    Base,
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    TenantScopedMixin,
)


class AssetStatus(str, enum.Enum):
    PENDING = "pending"
    GENERATING = "generating"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SUPERSEDED = "superseded"


class TaskType(str, enum.Enum):
    CHAT = "chat"            # 文本（Brief 解析等）
    VISION = "vision"        # 视觉理解/评分
    IMAGE = "image"          # 文生图
    VIDEO = "video"          # 图生视频
    EMBED = "embed"          # 向量化


class GenerationStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PrevizAsset(Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantScopedMixin):
    __tablename__ = "previz_assets"

    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    combo_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    template_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    prompt_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    seed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    params: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    file_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    thumbnail_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    video_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), default=AssetStatus.PENDING.value, index=True
    )
    quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    quality_detail: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    ai_ratio: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    project: Mapped["Project"] = relationship(back_populates="previz_assets")


class GenerationTask(Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantScopedMixin):
    __tablename__ = "generation_tasks"

    project_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    asset_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    task_type: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    params: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default=GenerationStatus.QUEUED.value, index=True
    )
    queue: Mapped[str] = mapped_column(String(32), default="default", index=True)
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    external_task_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    started_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    finished_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
