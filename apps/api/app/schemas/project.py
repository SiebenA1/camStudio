"""项目与 Brief 相关 schema。"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    brand: str | None = None
    description: str | None = None
    budget: float | None = None
    timeline: dict | None = None


class ProjectUpdate(BaseModel):
    name: str | None = None
    brand: str | None = None
    description: str | None = None
    budget: float | None = None
    timeline: dict | None = None
    status: str | None = None


class ProjectOut(ORMModel):
    id: str
    tenant_id: str
    name: str
    brand: str | None
    status: str
    owner_id: str | None
    budget: float | None
    timeline: dict | None
    description: str | None
    created_at: datetime
    updated_at: datetime


class BriefImportRequest(BaseModel):
    source_type: str = "text"
    raw_text: str = ""
    filename: str | None = None


class VariableOut(ORMModel):
    id: str
    project_id: str
    type: str
    options: list
    selected: list
    weight: float
    sort: int


class VariableUpdate(BaseModel):
    options: list | None = None
    selected: list | None = None
    weight: float | None = None
    sort: int | None = None


class ComboCreate(BaseModel):
    combo: dict
    weight: float = 1.0
