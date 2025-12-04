from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.services.auth_service import require_role
from backend.services.external_sync_service import sync_external_metadata

router = APIRouter(
    prefix="/admin",
    tags=["admin-sync"],
)


@router.post("/sync-external")
async def admin_sync_external(
    _: None = Depends(require_role("admin")),
):
    """Admin-only endpoint to trigger external metadata sync.

    Response payload:
    {
      "items_updated": <int>,
      "timestamp": "<ISO-8601 string>"
    }
    """
    updated_count, timestamp = await sync_external_metadata()
    return {
        "items_updated": updated_count,
        "timestamp": timestamp,
    }
