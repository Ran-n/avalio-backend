#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/04/09 14:11:10.576197
Revised: 2026/04/09 14:11:10.576197
"""

from fastapi import FastAPI

from app.config import settings
from app.core.exceptions import AvalioError, avalio_exception_handler
from app.routers import admin, audit, auth, classes, evaluations, students

app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_exception_handler(AvalioError, avalio_exception_handler)

app.include_router(auth.router, prefix=settings.api_v1_prefix)
app.include_router(admin.router, prefix=settings.api_v1_prefix)
app.include_router(students.router, prefix=settings.api_v1_prefix)
app.include_router(classes.router, prefix=settings.api_v1_prefix)
app.include_router(evaluations.router, prefix=settings.api_v1_prefix)
app.include_router(audit.router, prefix=settings.api_v1_prefix)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "app": settings.app_name}
