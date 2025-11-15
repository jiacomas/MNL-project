"""
Admin router for syncing external metadata onto items/movies.
"""

from fastapi import APIRouter

from backend.services import external_sync_service

router = APIRouter()


@router.post("/admin/sync-external")
async def sync_external():
    """
    Triggers external metadata sync for items/movies.

    Acceptance Criteria:
    - Backend provides POST /admin/sync-external (admin only in future).
    - API fetches at least poster URL, runtime, and cast.
    - Synced data updates existing records in items.json (no duplicates).
    - Sync action is logged with timestamp + items updated.
    """
    updated_count, ts = await external_sync_service.sync_external_metadata()
    return {
        "message": "Sync completed",
        "items_updated": updated_count,
        "synced_at": ts.isoformat(),
    }
