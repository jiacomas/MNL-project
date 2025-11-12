"""
Admin analytics endpoints.

Provides CSV export of platform statistics for offline analysis.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from backend.services import analytics_service

router = APIRouter()


@router.get("/admin/export-stats", response_class=FileResponse)
def export_stats():
    """
    Exports platform statistics as a CSV file.

    Acceptance Criteria:
    - Export includes user counts, reviews, bookmarks, penalties, top 10 genres.
    - Export format: CSV with stable schema and headers.
    - CSV includes generated_at timestamp.
    """
    stats = analytics_service.compute_stats()
    csv_path = analytics_service.write_stats_csv(stats)

    if not csv_path.exists():
        raise HTTPException(status_code=500, detail="Failed to generate CSV")

    return FileResponse(
        path=str(csv_path),
        media_type="text/csv",
        filename=csv_path.name,
    )
