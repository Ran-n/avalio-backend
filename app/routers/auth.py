#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/04/09 14:11:11.350022
Revised: 2026/04/09 14:11:11.350022
"""

import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.config import settings
from app.core.dependencies import get_current_user, get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.user import ChangePasswordRequest, RefreshRequest, TokenResponse
from app.services import audit

router = APIRouter(prefix="/auth", tags=["auth"])

_DUMMY_HASH = "$2b$12$aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"


@router.post("/login", response_model=TokenResponse)
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> TokenResponse:
    user = db.query(User).filter(User.username == form_data.username).first()
    if user is None:
        verify_password(form_data.password, _DUMMY_HASH)  # constant-time: avoid user enumeration
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not verify_password(form_data.password, user.hashed_password):
        audit.log(
            db,
            action="auth.login.failed",
            actor_id=user.id,
            ip_address=request.client.host if request.client else None,
        )
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")
    if not user.is_approved:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Account pending approval"
        )

    access_token = create_access_token(user.id, user.role)
    raw_refresh = secrets.token_urlsafe(64)
    db.add(
        RefreshToken(
            token=raw_refresh,
            user_id=user.id,
            expires_at=datetime.now(timezone.utc)
            + timedelta(days=settings.refresh_token_expire_days),
        )
    )
    audit.log(
        db,
        action="auth.login",
        actor_id=user.id,
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    return TokenResponse(access_token=access_token, refresh_token=raw_refresh, role=user.role)


@router.post("/refresh", response_model=TokenResponse)
def refresh(body: RefreshRequest, db: Session = Depends(get_db)) -> TokenResponse:
    token_row = (
        db.query(RefreshToken)
        .filter(RefreshToken.token == body.refresh_token, RefreshToken.revoked.is_(False))
        .first()
    )
    if token_row is None or token_row.expires_at.replace(tzinfo=timezone.utc) < datetime.now(
        timezone.utc
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    token_row.revoked = True
    user = db.get(User, token_row.user_id)
    if user is None or not user.is_active or not user.is_approved:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )
    access_token = create_access_token(user.id, user.role)
    raw_refresh = secrets.token_urlsafe(64)
    db.add(
        RefreshToken(
            token=raw_refresh,
            user_id=user.id,
            expires_at=datetime.now(timezone.utc)
            + timedelta(days=settings.refresh_token_expire_days),
        )
    )
    db.commit()
    return TokenResponse(access_token=access_token, refresh_token=raw_refresh, role=user.role)


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    body: ChangePasswordRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    if not verify_password(body.current_password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")
    current_user.hashed_password = hash_password(body.new_password)
    for rt in current_user.refresh_tokens:
        rt.revoked = True
    audit.log(
        db,
        action="auth.change_password",
        actor_id=current_user.id,
        ip_address=request.client.host if request.client else None,
    )
    db.commit()


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    body: RefreshRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    token_row = (
        db.query(RefreshToken).filter(RefreshToken.token == body.refresh_token).first()
    )
    if token_row and token_row.user_id == current_user.id:
        token_row.revoked = True
    audit.log(db, action="auth.logout", actor_id=current_user.id)
    db.commit()
