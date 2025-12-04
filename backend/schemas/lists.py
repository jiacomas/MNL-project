from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ListBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class ListCreate(ListBase):
    pass


class ListUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class ListOut(ListBase):
    id: UUID
    user_id: str
    items: List[str] = []  # List of movie IDs
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ListItemAdd(BaseModel):
    movie_id: str
