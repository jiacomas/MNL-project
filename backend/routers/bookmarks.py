from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, status

from backend.deps import get_current_user_id, require_admin
from backend.schemas.bookmarks import BookmarkCreate, BookmarkOut
from backend.services import bookmarks_service as svc

router = APIRouter(prefix="/api/bookmarks", tags=["bookmarks"])

# --- User Endpoints ---


@router.get("/", response_model=List[BookmarkOut])
def list_my_bookmarks(user_id: str = Depends(get_current_user_id)):
    """List bookmarks for the current authenticated user."""
    return svc.list_bookmarks(user_id)


@router.get("/me", response_model=Optional[BookmarkOut])
def get_my_bookmark(
    movie_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """Return my bookmark for a specific movie."""
    return svc.get_user_bookmark(movie_id, user_id)


@router.post("/", response_model=BookmarkOut, status_code=status.HTTP_201_CREATED)
def create_bookmark(
    payload: BookmarkCreate, user_id: str = Depends(get_current_user_id)
):
    """Create a bookmark for the authenticated user."""
    return svc.create_bookmark(payload, user_id)


@router.delete("/me/{bookmark_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_bookmark(bookmark_id: str, user_id: str = Depends(get_current_user_id)):
    """Delete a bookmark owned by the current user."""
    svc.delete_bookmark(bookmark_id, user_id, is_admin=False)
    return None


# --- Admin Endpoints ---


@router.delete("/{bookmark_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bookmark_as_admin(
    bookmark_id: str,
    user_id: str = Depends(get_current_user_id),
    _=Depends(require_admin),
):
    svc.delete_bookmark(bookmark_id, user_id, is_admin=True)


@router.get("/export", dependencies=[Depends(require_admin)])
def export_bookmarks():
    """Export all bookmarks (admin only)."""
    return {"export_path": svc.export_bookmarks()}


@router.get(
    "/movie/{movie_id}",
    response_model=List[BookmarkOut],
    dependencies=[Depends(require_admin)],
)
def list_users_for_movie(movie_id: str):
    """Return all bookmarks for a specific movie (admin only)."""
    return svc.list_bookmarks_for_movie(movie_id)


# --- Public Endpoint ---


@router.get("/movie/{movie_id}/users/count")
def count_bookmarks(movie_id: str):
    """Return how many users bookmarked the movie (public)."""
    return {"count": svc.count_bookmarks_for_movie(movie_id)}
