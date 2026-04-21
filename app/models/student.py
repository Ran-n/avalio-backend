#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/04/09 14:11:10.983937
Revised: 2026/04/09 14:11:10.983937
"""

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    first_name: Mapped[str] = mapped_column(String(128), nullable=False)
    last_name: Mapped[str] = mapped_column(String(128), nullable=False)
    student_code: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    created_by_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    archived_by_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )

    created_by: Mapped["User"] = relationship("User", foreign_keys=[created_by_id])
    archived_by: Mapped["User | None"] = relationship("User", foreign_keys=[archived_by_id])
    class_enrollments: Mapped[list["ClassStudent"]] = relationship(
        "ClassStudent", back_populates="student", cascade="all, delete-orphan"
    )
    evaluation_entries: Mapped[list["EvaluationEntry"]] = relationship(
        "EvaluationEntry", back_populates="student"
    )
