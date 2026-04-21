#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/04/09 14:11:14.269977
Revised: 2026/04/09 14:11:14.269977
"""

from app.core.security import hash_password
from app.database import SessionLocal
from app.models.user import User, UserRole


def main() -> None:
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == "rut").first()
        if existing:
            print("User 'rut' already exists, skipping.")
            return
        admin = User(
            username="rut",
            email="rut@localhost",
            hashed_password=hash_password("testing"),
            role=UserRole.admin,
            is_approved=True,
            is_active=True,
        )
        db.add(admin)
        db.commit()
        print("Admin user 'rut' created.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
