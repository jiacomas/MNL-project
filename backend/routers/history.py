from __future__ import annotations

from fastapi import APIRouter, Depends, status

from backend.services import history_service
from backend.services.auth_service import get_current_user  # whatever you already use

router = APIRouter(prefix="/me/history", tags=["history"])


@router.get("/", status_code=status.HTTP_200_OK)
def get_my_history(current_user=Depends(get_current_user)):
    return history_service.list_history(current_user.user_id)


@router.post("/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
def log_view(movie_id: str, current_user=Depends(get_current_user)):
    history_service.log_view(current_user.user_id, movie_id)
    return


@router.delete("/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
def clear_one(movie_id: str, current_user=Depends(get_current_user)):
    history_service.clear_history_item(current_user.user_id, movie_id)
    return


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
def clear_all(current_user=Depends(get_current_user)):
    history_service.clear_history(current_user.user_id)
    return
