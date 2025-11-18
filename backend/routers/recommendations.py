from __future__ import annotations

from fastapi import APIRouter
from services import recommendations_service as svc

from schemas.recommendations import RecommendationOut

router = APIRouter(prefix="/users", tags=["recommendations"])


@router.get("/{user_id}/recommendations", response_model=list[RecommendationOut])
def get_user_recommendations(user_id: str) -> list[RecommendationOut]:
    """Return movie recommendations for a given user."""
    return svc.get_recommendations_for_user(user_id)
