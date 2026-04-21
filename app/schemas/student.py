#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/04/09 14:11:11.991494
Revised: 2026/04/09 14:11:11.991494
"""

from datetime import datetime

from pydantic import BaseModel


class StudentCreate(BaseModel):
    first_name: str
    last_name: str
    student_code: str | None = None


class StudentUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    student_code: str | None = None


class StudentRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    first_name: str
    last_name: str
    student_code: str | None
    is_active: bool
    created_at: datetime
    created_by_id: int
