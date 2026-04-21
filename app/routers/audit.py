#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/04/09 14:11:11.279003
Revised: 2026/04/09 14:11:11.279003
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_admin
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.audit_log import AuditLogRead

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/", response_model=list[AuditLogRead])
def list_audit_logs(
    actor_id: int | None = Query(None),
    action: str | None = Query(None),
    target_type: str | None = Query(None),
    target_id: int | None = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> list[AuditLog]:
    q = db.query(AuditLog)
    if actor_id is not None:
        q = q.filter(AuditLog.actor_id == actor_id)
    if action is not None:
        q = q.filter(AuditLog.action.contains(action))
    if target_type is not None:
        q = q.filter(AuditLog.target_type == target_type)
    if target_id is not None:
        q = q.filter(AuditLog.target_id == target_id)
    return q.order_by(AuditLog.timestamp.desc()).offset(offset).limit(limit).all()
