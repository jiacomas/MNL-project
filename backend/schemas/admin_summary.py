from __future__ import annotations

from pydantic import BaseModel


class AdminSummary(BaseModel):
    users_total: int
    active_users_24h: int
    reviews_total: int
