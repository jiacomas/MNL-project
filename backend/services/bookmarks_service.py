# backend/services/bookmarks_service.py
from __future__ import annotations

from typing import List, Optional

from fastapi import HTTPException, status

from backend.repositories.bookmarks_repo import JSONBookmarkRepo
from backend.schemas.bookmarks import BookmarkCreate, BookmarkOut

# Single shared repo
_repo = JSONBookmarkRepo()

# Internal helpers


def _find_for_user_and_movie(user_id: str, movie_id: str) -> Optional[BookmarkOut]:
    """Return existing bookmark for (user_id, movie_id), or None."""
    items = _repo.get_bookmarks_by_user(user_id)
    for b in items:
        if b.movie_id == movie_id:
            return b
    return None


# Public API
# Create


def create_bookmark(payload: BookmarkCreate, user_id: str) -> BookmarkOut:
    """
    Create a bookmark for the authenticated user.

    - Payload now only includes `movie_id`.
    - `user_id` MUST come from JWT.
    - Same (user, movie) pair must not repeat.
    """
    duplicate = _find_for_user_and_movie(user_id, payload.movie_id)
    if duplicate is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bookmark already exists for this user and movie.",
        )

    # repo does ID + timestamps automatically, we only pass fields
    return _repo.create(bookmark_in=payload, user_id=user_id)


# Read / List


def list_bookmarks(user_id: Optional[str] = None) -> List[BookmarkOut]:
    """
    List bookmarks:
    - If user_id is provided → filter to that user.
    - If None → return all bookmarks (admin/debug only).
    """
    if user_id is not None:
        return _repo.get_bookmarks_by_user(user_id)
    return _repo.list_all()


def get_user_bookmark(movie_id: str, user_id: str) -> Optional[BookmarkOut]:
    """Return the user's bookmark for a specific movie, or None."""
    return _find_for_user_and_movie(user_id, movie_id)


def count_bookmarks_for_movie(movie_id: str) -> int:
    """Return how many users bookmarked a given movie."""
    return len(_repo.get_bookmarks_by_movie(movie_id))


def delete_bookmark(bookmark_id: str, user_id: str, is_admin: bool = False) -> None:
    """
    Delete a bookmark.

    - Only the owner or an admin may delete.
    - If not found → 404
    """

    # First try to find ANY bookmark with this ID (scan repo)
    all_bookmarks = _repo.list_all()
    match = next((b for b in all_bookmarks if str(b.id) == str(bookmark_id)), None)

    if match is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bookmark not found.",
        )

    # Permission check (owner OR admin)
    if not is_admin and match.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this bookmark.",
        )

    _repo.delete(bookmark_id)


def list_bookmarks_for_movie(movie_id: str) -> List[BookmarkOut]:
    return _repo.get_bookmarks_by_movie(movie_id)


def export_bookmarks() -> str:
    """Export all bookmarks to a CSV file. (router restricts to admin)."""
    return _repo.export_to_csv()
