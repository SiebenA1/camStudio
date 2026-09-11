"""审计日志辅助。"""
from __future__ import annotations

from app.models.model_config import AuditLog


def write_audit(
    db,
    *,
    tenant_id: str,
    action: str,
    entity: str,
    entity_id: str | None = None,
    actor_id: str | None = None,
    actor_name: str | None = None,
    before: dict | None = None,
    after: dict | None = None,
    ip: str | None = None,
    detail: str | None = None,
) -> AuditLog:
    log = AuditLog(
        tenant_id=tenant_id,
        action=action,
        entity=entity,
        entity_id=entity_id,
        actor_id=actor_id,
        actor_name=actor_name,
        before=before,
        after=after,
        ip=ip,
        detail=detail,
    )
    db.add(log)
    return log
