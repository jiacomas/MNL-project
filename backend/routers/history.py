from __future__ import annotations

from typing import List

from fastapi import APIRouter, status

from backend.schemas.history import HistoryEntryOut
from backend.services import history_service

router = APIRouter(
    prefix="/history",
    tags=["history"],
)


@router.post(
    "/{user_id}/{movie_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
def log_view(user_id: str, movie_id: str) -> None:
    """Log that `user_id` viewed `movie_id`.

    Intended to be called when a movie detail page is opened.
    """
    history_service.log_view(user_id=user_id, movie_id=movie_id)


@router.get(
    "/{user_id}",
    response_model=List[HistoryEntryOut],
)
def list_history(user_id: str) -> List[HistoryEntryOut]:
    """Return the viewing history for a user, newest first."""
    entries = history_service.list_history(user_id=user_id)
    # entries are plain dicts; Pydantic will validate/convert
    return [HistoryEntryOut(**entry) for entry in entries]


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
def clear_history(user_id: str) -> None:
    """Clear *all* viewing history for a user."""
    history_service.clear_history(user_id=user_id)


@router.delete(
    "/{user_id}/{movie_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
def clear_history_item(user_id: str, movie_id: str) -> None:
    """Remove a single movie from the user's viewing history."""
    history_service.clear_history_item(user_id=user_id, movie_id=movie_id)
