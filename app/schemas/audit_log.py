#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/04/09 14:11:11.714097
Revised: 2026/04/09 14:11:11.714097
"""

from datetime import datetime

from pydantic import BaseModel


class AuditLogRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    actor_id: int | None
    action: str
    target_type: str | None
    target_id: int | None
    detail: str | None
    timestamp: datetime
    ip_address: str | None
