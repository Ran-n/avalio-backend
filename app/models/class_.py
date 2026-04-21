#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/04/09 14:11:10.734452
Revised: 2026/04/09 14:11:10.734452
"""

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Class(Base):
    __tablename__ = "classes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    year: Mapped[str] = mapped_column(String(16), nullable=False)
    teacher_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    teacher: Mapped["User"] = relationship(
        "User", back_populates="classes", foreign_keys=[teacher_id]
    )
    students: Mapped[list["ClassStudent"]] = relationship(
        "ClassStudent", back_populates="class_", cascade="all, delete-orphan"
    )
    evaluations: Mapped[list["Evaluation"]] = relationship(
        "Evaluation", back_populates="class_", cascade="all, delete-orphan"
    )


class ClassStudent(Base):
    __tablename__ = "class_students"

    class_id: Mapped[int] = mapped_column(Integer, ForeignKey("classes.id"), primary_key=True)
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("students.id"), primary_key=True)
    enrolled_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    class_: Mapped["Class"] = relationship("Class", back_populates="students")
    student: Mapped["Student"] = relationship("Student", back_populates="class_enrollments")
