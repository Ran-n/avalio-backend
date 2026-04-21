#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/04/09 14:11:11.801882
Revised: 2026/04/09 14:11:11.801882
"""

from datetime import datetime

from pydantic import BaseModel


class ClassCreate(BaseModel):
    name: str
    year: str
    teacher_id: int | None = None  # admins can assign to any teacher


class ClassRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str
    year: str
    teacher_id: int
    is_active: bool
    created_at: datetime


class ClassStudentAdd(BaseModel):
    student_id: int
