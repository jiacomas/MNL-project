# backend/services/bookmarks_service.py
from __future__ import annotations

from typing import List

from fastapi import HTTPException, status

from backend.repositories.bookmarks_repo import JSONBookmarkRepo
from backend.schemas.bookmarks import BookmarkCreate, BookmarkOut


class BookmarkService:
    '''
    Service layer for all bookmark-related business logic.

    This class wraps the JSONBookmarkRepo and is responsible for:
    - Enforcing “one bookmark per user+movie” rule
    - Providing filtered listing helpers
    - Centralizing delete / not-found behavior
    - Exposing a simple API for routers / other callers
    '''

    def __init__(self, repo: JSONBookmarkRepo) -> None:
        self.repo = repo

    # Internal helpers

    def _find_for_user_and_movie(
        self,
        user_id: str,
        movie_id: str,
    ) -> BookmarkOut | None:
        '''
        Return the existing bookmark for (user_id, movie_id) if it exists,
        otherwise None.
        '''
        existing = self.repo.get_by_user(user_id)
        for b in existing:
            if b.movie_id == movie_id:
                return b
        return None

    # Create

    def create_bookmark(self, payload: BookmarkCreate) -> BookmarkOut:
        '''
        Create a new bookmark.

        - A user must NOT bookmark the same movie more than once.
        - If a duplicate is detected, raise 409 Conflict.
        '''
        duplicate = self._find_for_user_and_movie(
            user_id=payload.user_id,
            movie_id=payload.movie_id,
        )
        if duplicate is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Bookmark already exists for this user and movie.",
            )

        return self.repo.create(payload)

    # Read / List

    def list_all(self) -> List[BookmarkOut]:
        '''
        Return all bookmarks in the system.
        Typically only used by admin/debug paths.
        '''
        return self.repo.list_all()

    def list_for_user(self, user_id: str) -> List[BookmarkOut]:
        '''
        Return all bookmarks created by a given user.
        '''
        return self.repo.get_by_user(user_id)

    def list_bookmarks(self, user_id: str | None = None) -> List[BookmarkOut]:
        '''
        Public listing API:

        - If user_id is provided → filter to that user.
        - If user_id is None    → return all bookmarks.
        '''
        if user_id:
            return self.list_for_user(user_id)
        return self.list_all()

    # Delete

    def delete_bookmark(self, bookmark_id: str) -> None:
        '''
        Delete a bookmark by ID.

        - If the bookmark existed → delete and return None.
        - If no bookmark was found → raise 404 Not Found.
        '''
        deleted = self.repo.delete(bookmark_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bookmark not found.",
            )

    # Export
    def export_bookmarks(self) -> str:
        '''
        Export all bookmarks to a CSV file.
        Returns:
            The path to the exported CSV file (as a string).
        '''
        return self.repo.export_to_csv()
