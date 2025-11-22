from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query, Response, status

from backend.schemas.penalties import (
    PenaltyCreate,
    PenaltyListResponse,
    PenaltyOut,
    PenaltySearchFilters,
    PenaltyUpdate,
    UserPenaltySummary,
)
from backend.services import penalties_services
from backend.deps import require_admin
from backend.services.auth_service import get_current_user

router = APIRouter(
    prefix="/penalties",
    tags=["penalties"],
)


# ---------- Utility: Get authentication context ----------

def get_auth_context(user: dict = Depends(get_current_user)) -> dict:
    """
    Extract user_id and is_admin flag from the JWT token payload.
    This context is passed to service layer so that service functions
    can enforce authorization logic.
    """
    return {
        "user_id": user.get("user_id"),
        "is_admin": user.get("role") == "admin",
    }


# ---------- Create / Update / Delete / Deactivate ----------

@router.post(
    "/",
    response_model=PenaltyOut,
    status_code=status.HTTP_201_CREATED,
)
def create_penalty_endpoint(
    payload: PenaltyCreate,
    _: dict = Depends(require_admin),
):
    """
    Create a new penalty record (admin only).
    Router ensures admin role, service performs additional admin validation.
    """
    return penalties_services.create_penalty(
        payload=payload,
        is_admin=True,
    )


@router.patch(
    "/{penalty_id}",
    response_model=PenaltyOut,
)
def update_penalty_endpoint(
    penalty_id: str,
    payload: PenaltyUpdate,
    _: dict = Depends(require_admin),
):
    """
    Update an existing penalty (admin only).
    """
    return penalties_services.update_penalty(
        penalty_id=penalty_id,
        payload=payload,
        is_admin=True,
    )


@router.delete(
    "/{penalty_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_penalty_endpoint(
    penalty_id: str,
    _: dict = Depends(require_admin),
):
    """
    Delete a penalty record (admin only).
    Returns 204 No Content to match REST conventions.
    """
    penalties_services.delete_penalty(
        penalty_id=penalty_id,
        is_admin=True,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{penalty_id}/deactivate",
    status_code=status.HTTP_204_NO_CONTENT,
)
def deactivate_penalty_endpoint(
    penalty_id: str,
    _: dict = Depends(require_admin),
):
    """
    Mark a penalty as inactive (admin only).
    """
    penalties_services.deactivate_penalty(
        penalty_id=penalty_id,
        is_admin=True,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------- Global search (admin only) ----------
# IMPORTANT: this must be defined BEFORE `/{penalty_id}` to avoid route conflicts.

@router.get(
    "/search",
    response_model=PenaltyListResponse,
)
def search_penalties_endpoint(
    user_id: Optional[str] = Query(None),
    penalty_type: Optional[str] = Query(None),
    severity: Optional[int] = Query(None),
    is_active: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    _: dict = Depends(require_admin),
):
    """
    Global search across all users' penalties (admin only).
    Supported filters:
    - user_id
    - penalty_type
    - severity
    - is_active
    Includes pagination.
    """
    filters = PenaltySearchFilters(
        user_id=user_id,
        penalty_type=penalty_type,
        severity=severity,
        is_active=is_active,
    )

    return penalties_services.search_penalties(
        filters=filters,
        page=page,
        page_size=page_size,
        is_admin=True,
    )


# ---------- Retrieve a single penalty ----------

@router.get(
    "/{penalty_id}",
    response_model=PenaltyOut,
)
def get_penalty_endpoint(
    penalty_id: str,
    auth_ctx: dict = Depends(get_auth_context),
):
    """
    Retrieve a specific penalty.
    - Admin users can access any penalty.
    - Regular users can only access penalties belonging to themselves.
    Authorization logic is handled by the service layer.
    """
    return penalties_services.get_penalty(
        penalty_id=penalty_id,
        caller_user_id=auth_ctx["user_id"],
        is_admin=auth_ctx["is_admin"],
    )


# ---------- User-level listing and summary ----------

@router.get(
    "/users/{user_id}",
    response_model=PenaltyListResponse,
)
def list_penalties_for_user_endpoint(
    user_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    auth_ctx: dict = Depends(get_auth_context),
):
    """
    List all penalties associated with a specific user.
    - Admin users can list penalties for any user.
    - Regular users can only list their own penalties.
    """
    return penalties_services.list_penalties_for_user(
        user_id=user_id,
        caller_user_id=auth_ctx["user_id"],
        is_admin=auth_ctx["is_admin"],
        page=page,
        page_size=page_size,
    )


@router.get(
    "/users/{user_id}/summary",
    response_model=UserPenaltySummary,
)
def get_user_penalty_summary_endpoint(
    user_id: str,
    auth_ctx: dict = Depends(get_auth_context),
):
    """
    Retrieve penalty summary (e.g., totals, active penalties, etc.) for a user.
    - Admin users can access any summary.
    - Regular users can only access their own.
    """
    return penalties_services.get_user_penalty_summary(
        user_id=user_id,
        caller_user_id=auth_ctx["user_id"],
        is_admin=auth_ctx["is_admin"],
    )
