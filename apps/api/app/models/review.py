"""评审、批注、投票、审批模型。"""
from __future__ import annotations

import enum

from sqlalchemy import JSON, Integer, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantScopedMixin


class ReviewType(str, enum.Enum):
    INTERNAL = "internal"
    CLIENT = "client"


class ReviewDecision(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ON_HOLD = "on_hold"


class Review(Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantScopedMixin):
    __tablename__ = "reviews"

    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    asset_ids: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    reviewer_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    type: Mapped[str] = mapped_column(String(16), default=ReviewType.INTERNAL.value)
    status: Mapped[str] = mapped_column(String(32), default="open", nullable=False)
    decision: Mapped[str] = mapped_column(String(32), default=ReviewDecision.PENDING.value)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    share_token: Mapped[str | None] = mapped_column(String(128), index=True, nullable=True)
    expires_at: Mapped[str | None] = mapped_column(String(64), nullable=True)

    comments: Mapped[list["ReviewComment"]] = relationship(
        back_populates="review", cascade="all, delete-orphan"
    )
    votes: Mapped[list["ReviewVote"]] = relationship(
        back_populates="review", cascade="all, delete-orphan"
    )
    approvals: Mapped[list["Approval"]] = relationship(
        back_populates="review", cascade="all, delete-orphan"
    )


class ReviewComment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "review_comments"

    review_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("reviews.id", ondelete="CASCADE"), index=True
    )
    author_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    author_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    asset_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    kind: Mapped[str] = mapped_column(String(16), default="text", nullable=False)
    shape: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # 批注几何信息
    text: Mapped[str] = mapped_column(Text, default="", nullable=False)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1-5 星
    resolved: Mapped[bool] = mapped_column(default=False, nullable=False)

    review: Mapped["Review"] = relationship(back_populates="comments")


class ReviewVote(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "review_votes"

    review_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("reviews.id", ondelete="CASCADE"), index=True
    )
    voter_key: Mapped[str] = mapped_column(String(128), nullable=False)
    asset_id: Mapped[str] = mapped_column(String(36), nullable=False)
    vote: Mapped[str] = mapped_column(String(16), default="like", nullable=False)

    review: Mapped["Review"] = relationship(back_populates="votes")


class Approval(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "approvals"

    review_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("reviews.id", ondelete="CASCADE"), index=True
    )
    actor_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    actor_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    decision: Mapped[str] = mapped_column(String(32), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    esign_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)

    review: Mapped["Review"] = relationship(back_populates="approvals")
