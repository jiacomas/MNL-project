# backend/routers/bookmarks.py
from __future__ import annotations

import os
from typing import List

from fastapi import APIRouter, Depends, status

from backend.repositories.bookmarks_repo import JSONBookmarkRepo
from backend.schemas.bookmarks import BookmarkCreate, BookmarkOut
from backend.services.bookmarks_service import BookmarkService

router = APIRouter(
    prefix="/bookmarks",
    tags=["bookmarks"],
)


def get_bookmarks_service() -> BookmarkService:
    '''Provide BookmarkService with a repo using BOOKMARKS_PATH.'''
    storage_path = os.getenv("BOOKMARKS_PATH", "data/bookmarks.json")
    repo = JSONBookmarkRepo(storage_path=storage_path)
    return BookmarkService(repo)


# GET /bookmarks
@router.get("/", response_model=List[BookmarkOut])
def list_bookmarks(
    user_id: str | None = None,
    svc: BookmarkService = Depends(get_bookmarks_service),
) -> List[BookmarkOut]:
    '''
    List bookmarks.
    - If user_id is provided, return only that user's bookmarks.
    - If user_id is omitted, return all bookmarks (admin/debug use).
    '''
    return svc.list_bookmarks(user_id=user_id)


# POST /bookmarks
@router.post(
    "/",
    response_model=BookmarkOut,
    status_code=status.HTTP_200_OK,
)
def create_bookmark(
    payload: BookmarkCreate,
    svc: BookmarkService = Depends(get_bookmarks_service),
) -> BookmarkOut:
    '''
    Create a new bookmark.
    The repo is responsible for generating:
    - id (UUIDv4)
    - created_at / updated_at timestamps
    '''
    return svc.create_bookmark(payload)


# DELETE /bookmarks/{id}
@router.delete(
    "/{bookmark_id}",
    status_code=status.HTTP_200_OK,
)
def delete_bookmark(
    bookmark_id: str,
    svc: BookmarkService = Depends(get_bookmarks_service),
) -> dict:
    '''
    Delete a bookmark by its ID.
    - Returns 200 if deleted.
    - Returns 404 if the bookmark is not found by service
    '''
    svc.delete_bookmark(bookmark_id)
    return {"deleted": True}


# GET /bookmarks/export
@router.get("/export", status_code=status.HTTP_200_OK)
def export_bookmarks(
    svc: BookmarkService = Depends(get_bookmarks_service),
) -> dict:
    '''
    Export all bookmarks to a CSV file on disk.
    Returns a small JSON payload with the export path.
    '''
    export_path = svc.export_bookmarks()
    return {"export_path": export_path}
