from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, status

from backend.deps import get_current_user_id
from backend.schemas.lists import ListCreate, ListItemAdd, ListOut, ListUpdate
from backend.services import lists_service as svc

router = APIRouter(prefix="/api/lists", tags=["lists"])


@router.post("/", response_model=ListOut, status_code=status.HTTP_201_CREATED)
def create_list(
    payload: ListCreate,
    user_id: str = Depends(get_current_user_id),
):
    """Create a new list."""
    return svc.create_list(payload, user_id)


@router.get("/", response_model=List[ListOut])
def list_my_lists(user_id: str = Depends(get_current_user_id)):
    """Get all lists for the current user."""
    return svc.get_my_lists(user_id)


@router.get("/{list_id}", response_model=ListOut)
def get_list(
    list_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """Get a specific list."""
    return svc.get_list(list_id, user_id)


@router.patch("/{list_id}", response_model=ListOut)
def update_list(
    list_id: str,
    payload: ListUpdate,
    user_id: str = Depends(get_current_user_id),
):
    """Update a list."""
    return svc.update_list(list_id, payload, user_id)


@router.delete("/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_list(
    list_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """Delete a list."""
    svc.delete_list(list_id, user_id)
    return None


@router.post("/{list_id}/items", response_model=ListOut)
def add_item_to_list(
    list_id: str,
    payload: ListItemAdd,
    user_id: str = Depends(get_current_user_id),
):
    """Add a movie to the list."""
    return svc.add_movie_to_list(list_id, payload.movie_id, user_id)


@router.delete("/{list_id}/items/{movie_id}", response_model=ListOut)
def remove_item_from_list(
    list_id: str,
    movie_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """Remove a movie from the list."""
    return svc.remove_movie_from_list(list_id, movie_id, user_id)
