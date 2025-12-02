"""
Admin router for syncing external metadata onto items/movies.
"""

from fastapi import APIRouter, Depends

from backend.data_loader import load_movies_from_kaggle
from backend.services.auth_service import require_role
from backend.services.external_sync_service import external_sync_service

router = APIRouter(prefix="/admin", tags=["Admin Sync"])


@router.post("/sync-external")
async def sync_external_metadata(admin=Depends(require_role("admin"))):
    """
    Trigger a sync with the external movie metadata API.
    Updates local items with poster, runtime, cast.
    """
    count, timestamp = await external_sync_service.sync_external_metadata()
    # If timestamp is already a string, just return it.
    if isinstance(timestamp, str):
        synced = timestamp
    else:
        # Otherwise assume it's a datetime object
        synced = timestamp.isoformat()

    return {
        "synced_at": synced,
        "updated_items": count,
    }


@router.post("/load-kaggle")
async def load_kaggle_movies(admin=Depends(require_role("admin"))):
    """
    Download movies dataset from Kaggle and regenerate local movie data files.
    Heavy operation – intended for admin use only.
    """
    summary = load_movies_from_kaggle()
    return {
        "detail": "Kaggle movies dataset loaded successfully.",
        **summary,
    }
