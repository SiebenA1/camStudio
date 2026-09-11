"""评审相关 schema。"""
from __future__ import annotations

from pydantic import BaseModel, Field


class ReviewCreate(BaseModel):
    asset_ids: list[str] = Field(default_factory=list)
    title: str | None = None
    type: str = "internal"  # internal | client


class CommentCreate(BaseModel):
    asset_id: str | None = None
    kind: str = "text"  # pin | rect | arrow | text
    shape: dict | None = None
    text: str = ""
    score: int | None = Field(default=None, ge=1, le=5)


class VoteCreate(BaseModel):
    asset_id: str
    vote: str = "like"  # like | dislike


class ApprovalCreate(BaseModel):
    decision: str  # approved | rejected | on_hold
    comment: str | None = None


class CommentOut(BaseModel):
    id: str
    review_id: str
    author_id: str | None
    author_name: str | None
    asset_id: str | None
    kind: str
    shape: dict | None
    text: str
    score: int | None
    resolved: bool
    created_at: str
