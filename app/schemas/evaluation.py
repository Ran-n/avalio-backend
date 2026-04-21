#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/04/09 14:11:11.899483
Revised: 2026/04/09 14:11:11.899483
"""

from datetime import datetime

from pydantic import BaseModel


class EvaluationCreate(BaseModel):
    title: str
    description: str | None = None
    class_id: int


class EvaluationRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    title: str
    description: str | None
    class_id: int
    created_by_id: int
    created_at: datetime
    updated_at: datetime | None


class EvaluationEntryUpsert(BaseModel):
    grade: float | None = None
    note: str | None = None


class EvaluationEntryRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    evaluation_id: int
    student_id: int
    grade: float | None
    note: str | None
    version: int
    created_at: datetime
    updated_at: datetime | None
