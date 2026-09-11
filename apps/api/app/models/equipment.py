"""拍摄设备（相机/镜头）配置：每个租户一份，官方参数获取一次后缓存复用。"""
from __future__ import annotations

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantScopedMixin


class EquipmentProfile(Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantScopedMixin):
    __tablename__ = "equipment_profiles"

    camera_model: Mapped[str | None] = mapped_column(String(255), nullable=True)
    lens_model: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # 官方技术参数（由大模型获取一次后缓存）
    specs_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
