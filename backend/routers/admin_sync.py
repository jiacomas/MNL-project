"""
Admin router for syncing external metadata onto items/movies.
"""

from fastapi import APIRouter, Depends

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
    return {
        "synced_at": timestamp.isoformat(),
    }
