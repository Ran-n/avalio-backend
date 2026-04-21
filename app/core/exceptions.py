#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/04/09 14:11:10.263291
Revised: 2026/04/09 14:11:10.263291
"""

from fastapi import Request
from fastapi.responses import JSONResponse


class AvalioError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail


async def avalio_exception_handler(request: Request, exc: AvalioError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
