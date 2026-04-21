#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/04/09 14:11:11.421485
Revised: 2026/04/09 14:11:11.421485
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.models.class_ import Class, ClassStudent
from app.models.student import Student
from app.models.user import User, UserRole
from app.schemas.class_ import ClassCreate, ClassRead, ClassStudentAdd
from app.schemas.student import StudentRead
from app.services import audit

router = APIRouter(prefix="/classes", tags=["classes"])


@router.get("/", response_model=list[ClassRead])
def list_classes(
    limit: int = Query(100, le=500),
    offset: int = Query(0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Class]:
    if current_user.role == UserRole.admin:
        return (
            db.query(Class)
            .filter(Class.is_active.is_(True))
            .offset(offset)
            .limit(limit)
            .all()
        )
    return (
        db.query(Class)
        .filter(Class.teacher_id == current_user.id, Class.is_active.is_(True))
        .offset(offset)
        .limit(limit)
        .all()
    )


@router.post("/", response_model=ClassRead, status_code=status.HTTP_201_CREATED)
def create_class(
    body: ClassCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Class:
    teacher_id = (
        body.teacher_id
        if current_user.role == UserRole.admin and body.teacher_id
        else current_user.id
    )
    class_ = Class(name=body.name, year=body.year, teacher_id=teacher_id)
    db.add(class_)
    db.flush()
    audit.log(
        db,
        action="class.create",
        actor_id=current_user.id,
        target_type="class",
        target_id=class_.id,
        detail={"name": body.name, "year": body.year, "teacher_id": teacher_id},
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    db.refresh(class_)
    return class_


@router.get("/{class_id}/students", response_model=list[StudentRead])
def list_class_students(
    class_id: int,
    limit: int = Query(100, le=500),
    offset: int = Query(0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Student]:
    class_ = db.get(Class, class_id)
    if class_ is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
    if current_user.role == UserRole.teacher and class_.teacher_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your class")
    students = [enrollment.student for enrollment in class_.students]
    return students[offset : offset + limit]


@router.post("/{class_id}/students", status_code=status.HTTP_204_NO_CONTENT)
def add_student_to_class(
    class_id: int,
    body: ClassStudentAdd,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    class_ = db.get(Class, class_id)
    if class_ is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
    if current_user.role == UserRole.teacher and class_.teacher_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your class")
    if db.get(Student, body.student_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    if (
        db.query(ClassStudent)
        .filter(
            ClassStudent.class_id == class_id, ClassStudent.student_id == body.student_id
        )
        .first()
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Student already in class"
        )
    db.add(ClassStudent(class_id=class_id, student_id=body.student_id))
    audit.log(
        db,
        action="class.student.add",
        actor_id=current_user.id,
        target_type="class",
        target_id=class_id,
        detail={"student_id": body.student_id},
        ip_address=request.client.host if request.client else None,
    )
    db.commit()


@router.delete("/{class_id}/students/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_student_from_class(
    class_id: int,
    student_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    class_ = db.get(Class, class_id)
    if class_ is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
    if current_user.role == UserRole.teacher and class_.teacher_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your class")
    enrollment = (
        db.query(ClassStudent)
        .filter(ClassStudent.class_id == class_id, ClassStudent.student_id == student_id)
        .first()
    )
    if enrollment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Student not in class"
        )
    db.delete(enrollment)
    audit.log(
        db,
        action="class.student.remove",
        actor_id=current_user.id,
        target_type="class",
        target_id=class_id,
        detail={"student_id": student_id},
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
