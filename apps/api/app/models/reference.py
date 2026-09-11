"""空镜参考图模型：真实拍摄的空场景/空机位照片，作为图生预演的输入。"""
from __future__ import annotations

from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantScopedMixin


class ReferenceShot(Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantScopedMixin):
    __tablename__ = "reference_shots"

    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    file_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # 视觉模型对空镜图的场景分析结果
    analysis_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # 结合 Brief 生成的拍摄指导 + 要素
    guidance_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="uploaded", index=True)
