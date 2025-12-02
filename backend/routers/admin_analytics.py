"""
Admin analytics endpoints.

Provides CSV export of platform statistics for offline analysis.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse

from backend.services.analytics_service import analytics_service
from backend.services.auth_service import require_role

router = APIRouter(prefix="/admin/analytics", tags=["Admin Analytics"])


@router.get("/stats")
def get_platform_stats(admin=Depends(require_role("admin"))):
    """
    Return platform statistics:
    - users_count
    - reviews_count
    - bookmarks_count
    - penalties_count
    - top_genres (list of {genre, count})
    """
    metrics, top_genres = analytics_service.compute_stats()

    # Convert metrics list to dict for JSON response
    metrics_dict = {k: v for k, v in metrics}

    return {
        "metrics": metrics_dict,
        "top_genres": [{"genre": g, "count": c} for g, c in top_genres],
    }


@router.get("/stats/export")
def export_platform_stats(admin=Depends(require_role("admin"))):
    """
    Generate and download a CSV of platform stats.
    """
    path = analytics_service.compute_stats_and_write_csv()
    if not path.exists():
        raise HTTPException(status_code=500, detail="Failed to generate CSV")
    return FileResponse(
        path,
        media_type="text/csv",
        filename="analytics_export.csv",
    )


@router.get("/reviews/search")
def search_reviews(
    q: str = Query(..., min_length=1),
    sort: str = "date",  # date, rating
    order: str = "desc",  # asc, desc
    admin=Depends(require_role("admin")),
):
    """
    Search reviews by movie title (partial match).
    """
    return analytics_service.search_reviews_by_title(q, sort_by=sort, order=order)


@router.get("/reviews/export")
def export_reviews_search(
    q: str = Query(..., min_length=1),
    sort: str = "date",
    order: str = "desc",
    admin=Depends(require_role("admin")),
):
    """
    Search reviews and export results as CSV.
    """
    rows = analytics_service.search_reviews_by_title(q, sort_by=sort, order=order)
    path = analytics_service.write_reviews_csv(rows)
    if not path.exists():
        raise HTTPException(status_code=500, detail="Failed to generate CSV")
    return FileResponse(
        path,
        media_type="text/csv",
        filename="reviews_export.csv",
    )
