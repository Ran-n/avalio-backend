#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/04/09 14:11:10.813988
Revised: 2026/04/09 14:11:10.813988
"""

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Evaluation(Base):
    __tablename__ = "evaluations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    class_id: Mapped[int] = mapped_column(Integer, ForeignKey("classes.id"), nullable=False)
    created_by_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    class_: Mapped["Class"] = relationship("Class", back_populates="evaluations")
    created_by: Mapped["User"] = relationship("User", foreign_keys=[created_by_id])
    entries: Mapped[list["EvaluationEntry"]] = relationship(
        "EvaluationEntry", back_populates="evaluation", cascade="all, delete-orphan"
    )


class EvaluationEntry(Base):
    __tablename__ = "evaluation_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    evaluation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("evaluations.id"), nullable=False
    )
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("students.id"), nullable=False)
    grade: Mapped[float | None] = mapped_column(Float, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    evaluation: Mapped["Evaluation"] = relationship("Evaluation", back_populates="entries")
    student: Mapped["Student"] = relationship("Student", back_populates="evaluation_entries")
    created_by: Mapped["User"] = relationship("User", foreign_keys=[created_by_id])
    history: Mapped[list["EvaluationEntryHistory"]] = relationship(
        "EvaluationEntryHistory", back_populates="entry", cascade="all, delete-orphan"
    )


class EvaluationEntryHistory(Base):
    __tablename__ = "evaluation_entry_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    entry_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("evaluation_entries.id"), nullable=False
    )
    grade: Mapped[float | None] = mapped_column(Float, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    changed_by_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    changed_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    entry: Mapped["EvaluationEntry"] = relationship("EvaluationEntry", back_populates="history")
    changed_by: Mapped["User"] = relationship("User", foreign_keys=[changed_by_id])
