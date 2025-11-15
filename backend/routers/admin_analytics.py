"""
Admin analytics endpoints.

Provides CSV export of platform statistics for offline analysis.
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
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


@router.get("/admin/reviews")
def admin_search_reviews(
    title: Optional[str] = Query(
        None, description="Case-insensitive movie title search"
    ),
    sort: str = Query(
        "date", regex="^(date|rating)$", description="Sort by 'date' or 'rating'"
    ),
    order: str = Query(
        "desc", regex="^(asc|desc)$", description="Sort order: asc or desc"
    ),
    export: bool = Query(False, description="If true, return CSV file instead of JSON"),
):
    """Admin endpoint to search reviews by movie title and optionally export to CSV.

    Results include: id, movie_title, rating, created_at, user_id.
    """
    rows = analytics_service.search_reviews_by_title(
        title_query=title or "", sort_by=sort, order=order
    )

    if export:
        path = analytics_service.write_reviews_csv(rows)
        if not path.exists():
            raise HTTPException(status_code=500, detail="Failed to generate CSV")
        return FileResponse(path=str(path), media_type="text/csv", filename=path.name)

    return {"items": rows}
