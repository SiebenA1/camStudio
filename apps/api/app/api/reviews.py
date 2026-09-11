"""评审、批注、投票、审批路由。"""
from __future__ import annotations

import secrets

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.projects import _get_project
from app.core.errors import AppError, ok
from app.database import get_db
from app.models.previz import PrevizAsset
from app.models.review import Approval, Review, ReviewComment, ReviewVote
from app.models.tenant import User
from app.schemas.review import ApprovalCreate, CommentCreate, ReviewCreate, VoteCreate

router = APIRouter(tags=["reviews"])


def _comment_dict(c: ReviewComment) -> dict:
    return {
        "id": c.id, "review_id": c.review_id, "author_id": c.author_id,
        "author_name": c.author_name, "asset_id": c.asset_id, "kind": c.kind,
        "shape": c.shape, "text": c.text, "score": c.score, "resolved": c.resolved,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }


def _review_dict(r: Review) -> dict:
    return {
        "id": r.id, "project_id": r.project_id, "asset_ids": r.asset_ids,
        "reviewer_id": r.reviewer_id, "type": r.type, "status": r.status,
        "decision": r.decision, "title": r.title,
        "share_token": r.share_token, "expires_at": r.expires_at,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "comments": [_comment_dict(c) for c in r.comments],
        "votes": [{"id": v.id, "asset_id": v.asset_id, "vote": v.vote, "voter_key": v.voter_key} for v in r.votes],
        "approvals": [{"id": a.id, "actor_name": a.actor_name, "decision": a.decision,
                       "comment": a.comment, "created_at": a.created_at.isoformat() if a.created_at else None}
                      for a in r.approvals],
    }


def _get_review(db: Session, user: User, review_id: str) -> Review:
    r = db.get(Review, review_id)
    if not r:
        raise AppError(404, "not_found", "评审不存在")
    if r.tenant_id != user.tenant_id:
        raise AppError(403, "forbidden", "无权访问该评审")
    return r


@router.post("/projects/{project_id}/reviews")
def create_review(project_id: str, body: ReviewCreate, db: Session = Depends(get_db),
                  user: User = Depends(get_current_user)):
    _get_project(db, user, project_id)
    r = Review(
        tenant_id=user.tenant_id, project_id=project_id, asset_ids=body.asset_ids,
        reviewer_id=user.id, type=body.type, title=body.title, status="open",
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    return ok(_review_dict(r))


@router.get("/reviews/{review_id}")
def get_review(review_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    r = _get_review(db, user, review_id)
    data = _review_dict(r)
    # 组装资产
    assets = []
    for aid in r.asset_ids:
        a = db.get(PrevizAsset, aid)
        if a:
            assets.append({"id": a.id, "file_url": a.file_url, "prompt": a.prompt,
                           "model": a.model, "quality_score": a.quality_score})
    data["assets"] = assets
    return ok(data)


@router.post("/reviews/{review_id}/comments")
def add_comment(review_id: str, body: CommentCreate, db: Session = Depends(get_db),
                user: User = Depends(get_current_user)):
    _get_review(db, user, review_id)
    c = ReviewComment(
        review_id=review_id, author_id=user.id, author_name=user.name,
        asset_id=body.asset_id, kind=body.kind, shape=body.shape,
        text=body.text, score=body.score, resolved=False,
    )
    db.add(c)
    db.commit()
    return ok(_comment_dict(c))


@router.post("/reviews/{review_id}/votes")
def add_vote(review_id: str, body: VoteCreate, db: Session = Depends(get_db),
             user: User = Depends(get_current_user)):
    _get_review(db, user, review_id)
    v = ReviewVote(review_id=review_id, voter_key=user.id, asset_id=body.asset_id, vote=body.vote)
    db.add(v)
    db.commit()
    return ok({"id": v.id, "asset_id": v.asset_id, "vote": v.vote})


@router.post("/reviews/{review_id}/approvals")
def add_approval(review_id: str, body: ApprovalCreate, db: Session = Depends(get_db),
                 user: User = Depends(get_current_user)):
    r = _get_review(db, user, review_id)
    a = Approval(review_id=review_id, actor_id=user.id, actor_name=user.name,
                 decision=body.decision, comment=body.comment)
    db.add(a)
    if body.decision in ("approved", "rejected"):
        r.decision = body.decision
        r.status = "closed"
    elif body.decision == "on_hold":
        r.decision = "on_hold"
    db.commit()
    return ok({"id": a.id, "decision": a.decision, "review_decision": r.decision})


@router.post("/reviews/{review_id}/share")
def share_review(review_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    r = _get_review(db, user, review_id)
    if not r.share_token:
        r.share_token = secrets.token_urlsafe(24)
    r.type = "client"
    db.commit()
    return ok({"share_token": r.share_token, "url": f"/share/{r.share_token}"})


# ---- 公开分享（无需登录）----
public_router = APIRouter(tags=["share"])


@public_router.get("/share/{token}")
def view_share(token: str, db: Session = Depends(get_db)):
    r = db.query(Review).filter(Review.share_token == token).first()
    if not r:
        raise AppError(404, "not_found", "分享链接无效")
    assets = []
    for aid in r.asset_ids:
        a = db.get(PrevizAsset, aid)
        if a:
            assets.append({"id": a.id, "file_url": a.file_url, "prompt": a.prompt,
                           "model": a.model, "quality_score": a.quality_score})
    return ok({
        "review_id": r.id, "title": r.title, "decision": r.decision,
        "assets": assets,
        "votes": [{"asset_id": v.asset_id, "vote": v.vote} for v in r.votes],
    })
