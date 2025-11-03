"""
Schemas for the application using Pydantic models.
Defines Admin, Users, Movies, and Bookmark models.
"""

# pylint: disable=too-few-public-methods

from typing import List

from pydantic import BaseModel


class Admin(BaseModel):
    """Represents an admin user with ID and password hash."""

    id: str
    passwordHash: str


class Users(BaseModel):
    """Represents a user with ID, password, penalties, and bookmarks."""

    id: str
    passwordHash: str
    penalties: str
    bookmarks: List[str] = []


class Movies(BaseModel):
    """Represents a movie with title, category, and tags."""

    title: str
    category: str
    tags: List[str] = []


class Bookmark(BaseModel):
    """Represents bookmarks of a user with a list of movie IDs."""

    id: str
    movies: List[str] = []
