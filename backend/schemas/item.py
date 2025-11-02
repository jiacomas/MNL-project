from pydantic import BaseModel
from typing import List


class Admin(BaseModel):
    id: str
    passwordHash: str


class Users(BaseModel):
    id: str
    passwordHash: str
    penalties: str
    bookmarks: List[str] = []


class Movies(BaseModel):
    title: str
    category: str
    tags: List[str] = []


class Bookmark(BaseModel):
    id: str
    movies: List[str] = []
