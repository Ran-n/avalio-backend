#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/04/09 14:11:12.085462
Revised: 2026/04/09 14:11:12.085462
"""

from datetime import datetime

from pydantic import BaseModel, EmailStr

from app.models.user import UserRole


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: UserRole = UserRole.teacher
    is_approved: bool = False


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    is_active: bool | None = None
    is_approved: bool | None = None


class UserRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    username: str
    email: str
    role: UserRole
    is_approved: bool
    is_active: bool
    created_at: datetime
    created_by_id: int | None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: str


class RefreshRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class ResetPasswordRequest(BaseModel):
    new_password: str
