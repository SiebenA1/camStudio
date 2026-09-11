"""项目、Brief、变量、变量组合、Prompt 模板模型。"""
from __future__ import annotations

import enum

from sqlalchemy import JSON, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import (
    Base,
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    TenantScopedMixin,
    SoftDeleteMixin,
)
from app.models.tenant import project_members


class ProjectStatus(str, enum.Enum):
    DRAFT = "draft"
    BRIEFING = "briefing"
    PREVIZ = "previz"
    REVIEWING = "reviewing"
    LOCKED = "locked"
    SHOOTING = "shooting"
    POST = "post"
    DELIVERING = "delivering"
    DELIVERED = "delivered"
    ARCHIVED = "archived"


class VariableType(str, enum.Enum):
    CHARACTER = "character"      # 人物
    OUTFIT = "outfit"            # 穿搭
    SCENE = "scene"              # 场景
    POSE = "pose"                # 姿势
    EXPRESSION = "expression"    # 表情
    COMPOSITION = "composition"  # 构图


class BriefSourceType(str, enum.Enum):
    TEXT = "text"
    PDF = "pdf"
    PPT = "ppt"


class Project(Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantScopedMixin, SoftDeleteMixin):
    __tablename__ = "projects"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    brand: Mapped[str | None] = mapped_column(String(200), nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), default=ProjectStatus.DRAFT.value, index=True, nullable=False
    )
    owner_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    budget: Mapped[float | None] = mapped_column(Float, nullable=True)
    timeline: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    members: Mapped[list["User"]] = relationship(
        secondary=project_members, back_populates="projects"
    )
    brief: Mapped["Brief | None"] = relationship(back_populates="project", uselist=False)
    variables: Mapped[list["Variable"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    previz_assets: Mapped[list["PrevizAsset"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )


class Brief(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "briefs"

    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), unique=True, index=True
    )
    source_type: Mapped[str] = mapped_column(String(16), default=BriefSourceType.TEXT.value)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    parsed_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)

    project: Mapped["Project"] = relationship(back_populates="brief")


class Variable(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "variables"

    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    type: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    options: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    selected: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    sort: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    project: Mapped["Project"] = relationship(back_populates="variables")


class VariableCombo(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "variable_combos"

    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    combo: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)

    project: Mapped["Project"] = relationship()


class PromptTemplate(Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantScopedMixin, SoftDeleteMixin):
    __tablename__ = "prompt_templates"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    task_type: Mapped[str] = mapped_column(String(32), default="image", nullable=False)
    template: Mapped[str] = mapped_column(Text, nullable=False)
    brand_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
