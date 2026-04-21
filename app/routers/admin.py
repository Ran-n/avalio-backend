#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/04/09 14:11:11.208547
Revised: 2026/04/09 14:11:11.208547
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_admin
from app.core.security import hash_password
from app.models.user import User
from app.schemas.user import ResetPasswordRequest, UserCreate, UserRead
from app.services import audit

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=list[UserRead])
def list_users(
    limit: int = Query(100, le=500),
    offset: int = Query(0),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> list[User]:
    return db.query(User).offset(offset).limit(limit).all()


@router.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    body: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> User:
    if db.query(User).filter(User.username == body.username).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already taken")
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
        )
    user = User(
        username=body.username,
        email=body.email,
        hashed_password=hash_password(body.password),
        role=body.role,
        is_approved=body.is_approved,
        created_by_id=admin.id,
    )
    db.add(user)
    db.flush()
    audit.log(
        db,
        action="admin.user.create",
        actor_id=admin.id,
        target_type="user",
        target_id=user.id,
        detail={"username": body.username, "role": body.role},
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    db.refresh(user)
    return user


@router.patch("/users/{user_id}/approve", response_model=UserRead)
def approve_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.is_approved = True
    audit.log(
        db,
        action="admin.user.approve",
        actor_id=admin.id,
        target_type="user",
        target_id=user_id,
    )
    db.commit()
    db.refresh(user)
    return user


@router.patch("/users/{user_id}/reset-password", status_code=status.HTTP_204_NO_CONTENT)
def reset_user_password(
    user_id: int,
    body: ResetPasswordRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> None:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.hashed_password = hash_password(body.new_password)
    for rt in user.refresh_tokens:
        rt.revoked = True
    audit.log(
        db,
        action="admin.user.reset_password",
        actor_id=admin.id,
        target_type="user",
        target_id=user_id,
    )
    db.commit()


@router.patch("/users/{user_id}/deactivate", response_model=UserRead)
def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.is_active = False
    for rt in user.refresh_tokens:
        rt.revoked = True
    audit.log(
        db,
        action="admin.user.deactivate",
        actor_id=admin.id,
        target_type="user",
        target_id=user_id,
    )
    db.commit()
    db.refresh(user)
    return user
