from __future__ import annotations

from typing import List

from fastapi import HTTPException, status

from backend.repositories.lists_repo import JSONListRepo
from backend.schemas.lists import ListCreate, ListOut, ListUpdate

# Single shared repo
_repo = JSONListRepo()


def create_list(payload: ListCreate, user_id: str) -> ListOut:
    """Create a new list for the user."""
    return _repo.create(payload, user_id)


def get_my_lists(user_id: str) -> List[ListOut]:
    """Get all lists for the current user."""
    return _repo.get_by_user(user_id)


def get_list(list_id: str, user_id: str) -> ListOut:
    """Get a specific list, ensuring ownership."""
    lst = _repo.get_by_id(list_id)
    if not lst:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="List not found"
        )
    if lst.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized"
        )
    return lst


def update_list(list_id: str, payload: ListUpdate, user_id: str) -> ListOut:
    """Update a list, ensuring ownership."""
    get_list(list_id, user_id)  # Checks existence and ownership
    updated = _repo.update(list_id, payload)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="List not found"
        )
    return updated


def delete_list(list_id: str, user_id: str) -> None:
    """Delete a list, ensuring ownership."""
    get_list(list_id, user_id)  # Checks existence and ownership
    _repo.delete(list_id)


def add_movie_to_list(list_id: str, movie_id: str, user_id: str) -> ListOut:
    """Add a movie to a list, ensuring ownership."""
    get_list(list_id, user_id)  # Checks existence and ownership
    updated = _repo.add_item(list_id, movie_id)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="List not found"
        )
    return updated


def remove_movie_from_list(list_id: str, movie_id: str, user_id: str) -> ListOut:
    """Remove a movie from a list, ensuring ownership."""
    get_list(list_id, user_id)  # Checks existence and ownership
    updated = _repo.remove_item(list_id, movie_id)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="List not found"
        )
    return updated
