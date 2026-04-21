#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/04/09 14:11:11.565735
Revised: 2026/04/09 14:11:11.565735
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.models.class_ import ClassStudent
from app.models.student import Student
from app.models.user import User, UserRole
from app.schemas.student import StudentCreate, StudentRead, StudentUpdate
from app.services import audit

router = APIRouter(prefix="/students", tags=["students"])


def _assert_student_access(student: Student, current_user: User) -> None:
    if current_user.role == UserRole.admin:
        return
    teacher_class_ids = {c.id for c in current_user.classes}
    student_class_ids = {e.class_id for e in student.class_enrollments}
    if not teacher_class_ids.intersection(student_class_ids):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized for this student"
        )


@router.get("/", response_model=list[StudentRead])
def list_students(
    limit: int = Query(100, le=500),
    offset: int = Query(0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Student]:
    if current_user.role == UserRole.admin:
        return (
            db.query(Student)
            .filter(Student.is_active.is_(True))
            .offset(offset)
            .limit(limit)
            .all()
        )
    teacher_class_ids = [c.id for c in current_user.classes]
    return (
        db.query(Student)
        .join(ClassStudent, ClassStudent.student_id == Student.id)
        .filter(ClassStudent.class_id.in_(teacher_class_ids))
        .filter(Student.is_active.is_(True))
        .distinct()
        .offset(offset)
        .limit(limit)
        .all()
    )


@router.post("/", response_model=StudentRead, status_code=status.HTTP_201_CREATED)
def create_student(
    body: StudentCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Student:
    if body.student_code and db.query(Student).filter(
        Student.student_code == body.student_code
    ).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Student code already in use"
        )
    student = Student(
        first_name=body.first_name,
        last_name=body.last_name,
        student_code=body.student_code,
        created_by_id=current_user.id,
    )
    db.add(student)
    db.flush()
    audit.log(
        db,
        action="student.create",
        actor_id=current_user.id,
        target_type="student",
        target_id=student.id,
        detail={"name": f"{body.first_name} {body.last_name}"},
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    db.refresh(student)
    return student


@router.get("/{student_id}", response_model=StudentRead)
def get_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Student:
    student = db.get(Student, student_id)
    if student is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    _assert_student_access(student, current_user)
    return student


@router.patch("/{student_id}", response_model=StudentRead)
def update_student(
    student_id: int,
    body: StudentUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Student:
    student = db.get(Student, student_id)
    if student is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    _assert_student_access(student, current_user)
    changes = body.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(student, field, value)
    audit.log(
        db,
        action="student.update",
        actor_id=current_user.id,
        target_type="student",
        target_id=student_id,
        detail=changes,
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    db.refresh(student)
    return student


@router.delete("/{student_id}/archive", status_code=status.HTTP_204_NO_CONTENT)
def archive_student(
    student_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    student = db.get(Student, student_id)
    if student is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    _assert_student_access(student, current_user)
    student.is_active = False
    student.archived_at = datetime.now(timezone.utc)
    student.archived_by_id = current_user.id
    audit.log(
        db,
        action="student.archive",
        actor_id=current_user.id,
        target_type="student",
        target_id=student_id,
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
