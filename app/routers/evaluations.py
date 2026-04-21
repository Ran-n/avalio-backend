#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/04/09 14:11:11.495005
Revised: 2026/04/09 14:11:11.495005
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.models.class_ import Class
from app.models.evaluation import Evaluation, EvaluationEntry, EvaluationEntryHistory
from app.models.user import User, UserRole
from app.schemas.evaluation import (
    EvaluationCreate,
    EvaluationEntryRead,
    EvaluationEntryUpsert,
    EvaluationRead,
)
from app.services import audit

router = APIRouter(prefix="/evaluations", tags=["evaluations"])


def _assert_class_access(class_: Class, current_user: User) -> None:
    if current_user.role == UserRole.admin:
        return
    if class_.teacher_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your class")


@router.get("/", response_model=list[EvaluationRead])
def list_evaluations(
    class_id: int | None = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Evaluation]:
    q = db.query(Evaluation)
    if current_user.role == UserRole.teacher:
        teacher_class_ids = [c.id for c in current_user.classes]
        q = q.filter(Evaluation.class_id.in_(teacher_class_ids))
    if class_id is not None:
        q = q.filter(Evaluation.class_id == class_id)
    return q.offset(offset).limit(limit).all()


@router.post("/", response_model=EvaluationRead, status_code=status.HTTP_201_CREATED)
def create_evaluation(
    body: EvaluationCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Evaluation:
    class_ = db.get(Class, body.class_id)
    if class_ is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
    _assert_class_access(class_, current_user)
    evaluation = Evaluation(
        title=body.title,
        description=body.description,
        class_id=body.class_id,
        created_by_id=current_user.id,
    )
    db.add(evaluation)
    db.flush()
    audit.log(
        db,
        action="evaluation.create",
        actor_id=current_user.id,
        target_type="evaluation",
        target_id=evaluation.id,
        detail={"title": body.title, "class_id": body.class_id},
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    db.refresh(evaluation)
    return evaluation


@router.get("/{evaluation_id}/entries", response_model=list[EvaluationEntryRead])
def list_entries(
    evaluation_id: int,
    limit: int = Query(100, le=500),
    offset: int = Query(0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[EvaluationEntry]:
    evaluation = db.get(Evaluation, evaluation_id)
    if evaluation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluation not found")
    class_ = db.get(Class, evaluation.class_id)
    _assert_class_access(class_, current_user)
    return (
        db.query(EvaluationEntry)
        .filter(EvaluationEntry.evaluation_id == evaluation_id)
        .offset(offset)
        .limit(limit)
        .all()
    )


@router.put(
    "/{evaluation_id}/entries/{student_id}", response_model=EvaluationEntryRead
)
def upsert_entry(
    evaluation_id: int,
    student_id: int,
    body: EvaluationEntryUpsert,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EvaluationEntry:
    evaluation = db.get(Evaluation, evaluation_id)
    if evaluation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluation not found")
    class_ = db.get(Class, evaluation.class_id)
    _assert_class_access(class_, current_user)

    existing = (
        db.query(EvaluationEntry)
        .filter(
            EvaluationEntry.evaluation_id == evaluation_id,
            EvaluationEntry.student_id == student_id,
        )
        .first()
    )
    if existing:
        db.add(
            EvaluationEntryHistory(
                entry_id=existing.id,
                grade=existing.grade,
                note=existing.note,
                changed_by_id=current_user.id,
            )
        )
        existing.grade = body.grade
        existing.note = body.note
        existing.updated_at = datetime.now(timezone.utc)
        existing.version += 1
        entry = existing
        action = "evaluation.entry.update"
    else:
        entry = EvaluationEntry(
            evaluation_id=evaluation_id,
            student_id=student_id,
            grade=body.grade,
            note=body.note,
            created_by_id=current_user.id,
        )
        db.add(entry)
        action = "evaluation.entry.create"

    db.flush()
    audit.log(
        db,
        action=action,
        actor_id=current_user.id,
        target_type="evaluation_entry",
        target_id=entry.id,
        detail={"grade": body.grade, "note": body.note, "student_id": student_id},
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    db.refresh(entry)
    return entry
