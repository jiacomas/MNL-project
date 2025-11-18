# backend/routers/bookmarks.py
from __future__ import annotations

import os
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from backend.repositories.bookmarks_repo import JSONBookmarkRepo
from backend.schemas.bookmarks import BookmarkCreate, BookmarkOut

router = APIRouter(
    prefix="/bookmarks",
    tags=["bookmarks"],
)


def get_bookmarks_repo() -> JSONBookmarkRepo:
    '''FastAPI dependency that provides a JSONBookmarkRepo instance.'''
    storage_path = os.getenv("BOOKMARKS_PATH", "data/bookmarks.json")
    return JSONBookmarkRepo(storage_path=storage_path)


@router.get("/", response_model=List[BookmarkOut])
def list_bookmarks(
    user_id: str | None = None,
    repo: JSONBookmarkRepo = Depends(get_bookmarks_repo),
) -> List[BookmarkOut]:
    '''
    List bookmarks.
    - If user_id is provided, return only that user's bookmarks.
    - If user_id is omitted, return all bookmarks (admin/debug use).
    '''
    if user_id:
        return repo.get_by_user(user_id)
    return repo.list_all()


@router.post(
    "/",
    response_model=BookmarkOut,
    status_code=status.HTTP_200_OK,
)
def create_bookmark(
    payload: BookmarkCreate,
    repo: JSONBookmarkRepo = Depends(get_bookmarks_repo),
) -> BookmarkOut:
    '''
    Create a new bookmark.
    The repo is responsible for generating:
    - id (UUIDv4)
    - created_at / updated_at timestamps
    '''
    created = repo.create(payload)
    return created


@router.delete(
    "/{bookmark_id}",
    status_code=status.HTTP_200_OK,
)
def delete_bookmark(
    bookmark_id: str,
    repo: JSONBookmarkRepo = Depends(get_bookmarks_repo),
) -> None:
    '''
    Delete a bookmark by its ID.
    - Returns 204 if deleted.
    - Returns 404 if the bookmark is not found.
    '''
    deleted = repo.delete(bookmark_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bookmark not found.",
        )
    return {"deleted": True}


@router.get("/export", status_code=status.HTTP_200_OK)
def export_bookmarks(
    repo: JSONBookmarkRepo = Depends(get_bookmarks_repo),
) -> dict:
    '''
    Export all bookmarks to a CSV file on disk.
    Returns a small JSON payload with the export path.
    '''
    export_path = repo.export_to_csv()
    return {"export_path": export_path}
