from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import FileResponse

from backend.schemas.admin_summary import AdminSummary
from backend.services import admin_summary_service as svc

router = APIRouter(
    prefix="/admin/summary",
    tags=["admin-summary"],
)


@router.get("/", response_model=AdminSummary)
def get_summary() -> AdminSummary:
    """Real-time stats for admin dashboard summary cards."""
    data = svc.get_admin_summary()
    return AdminSummary(**data)


@router.get("/export.csv")
def export_summary_csv() -> FileResponse:
    """Export summary metrics as a CSV file."""
    path = svc.write_summary_csv()
    return FileResponse(
        path,
        media_type="text/csv",
        filename=path.name,
    )
