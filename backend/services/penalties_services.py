from __future__ import annotations

from typing import List, Optional

from fastapi import HTTPException, status

from backend.repositories.penalties_repo import JSONPenaltyRepository
from backend.schemas.penalties import (
    PenaltyCreate,
    PenaltyListResponse,
    PenaltyOut,
    PenaltySearchFilters,
    PenaltyUpdate,
    UserPenaltySummary,
)

# Default shared repository instance (can be overridden in tests)
_repo = JSONPenaltyRepository()


# ------------ Internal Utility Functions ------------


def _require_admin(is_admin: bool) -> None:
    """Raise 403 if the caller is not an admin."""
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can perform this action.",
        )


def _validate_pagination(page: int, page_size: int) -> None:
    """Validate pagination parameters; raise 400 if invalid."""
    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page must be greater than or equal to 1.",
        )
    if page_size < 1 or page_size > 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page size must be between 1 and 200.",
        )


def _build_list_response(
    items: List[PenaltyOut],
    total: int,
    page: int,
    page_size: int,
) -> PenaltyListResponse:
    """Wrap items + total count into a PenaltyListResponse model."""
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    return PenaltyListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


# ------------ Create / Update / Delete / Deactivate ------------


def create_penalty(
    payload: PenaltyCreate,
    *,
    is_admin: bool = False,
    repo: JSONPenaltyRepository = _repo,
) -> PenaltyOut:
    """
    Create a new penalty.

    - Only administrators can create penalties.
    - Rules for penalty_type and expires_at are validated at schema level.
    """
    _require_admin(is_admin)
    return repo.create(payload)


def update_penalty(
    penalty_id: str,
    payload: PenaltyUpdate,
    *,
    is_admin: bool = False,
    repo: JSONPenaltyRepository = _repo,
) -> PenaltyOut:
    """
    Update an existing penalty.

    - Only administrators can update penalties.
    - If the penalty does not exist, raise 404.
    """
    _require_admin(is_admin)
    updated = repo.update(penalty_id, payload)
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Penalty not found.",
        )
    return updated


def delete_penalty(
    penalty_id: str,
    *,
    is_admin: bool = False,
    repo: JSONPenaltyRepository = _repo,
) -> bool:
    """
    Permanently delete a penalty by its ID.

    - Only admins are allowed to delete penalties.
    - Raises 404 if the penalty does not exist.
    - Returns True when deletion succeeds.
    """
    _require_admin(is_admin)
    success = repo.delete(penalty_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Penalty not found.",
        )
    return True


def deactivate_penalty(
    penalty_id: str,
    *,
    is_admin: bool = False,
    repo: JSONPenaltyRepository = _repo,
) -> bool:
    """
    Manually deactivate a penalty (set is_active=False).

    - Only admins are allowed to deactivate penalties.
    - Raises 404 if the penalty does not exist.
    - Returns True when deactivation succeeds.
    """
    _require_admin(is_admin)
    success = repo.deactivate(penalty_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Penalty not found.",
        )
    return True


# ------------ Read / List / Search ------------


def get_penalty(
    penalty_id: str,
    *,
    caller_user_id: Optional[str] = None,
    is_admin: bool = False,
    repo: JSONPenaltyRepository = _repo,
) -> PenaltyOut:
    """
    Get a penalty by ID.

    - Administrators may view any penalty.
    - Non-admin users may only view their own penalties.
    """
    penalty = repo.get_by_id(penalty_id)
    if penalty is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Penalty not found.",
        )

    # Permission check for normal users
    if not is_admin and caller_user_id is not None:
        if penalty.user_id != caller_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this penalty.",
            )

    return penalty


def list_penalties_for_user(
    user_id: str,
    *,
    caller_user_id: Optional[str] = None,
    is_admin: bool = False,
    page: int = 1,
    page_size: int = 50,
    repo: JSONPenaltyRepository = _repo,
) -> PenaltyListResponse:
    """
    List all penalties for a specific user.

    - Admins may list penalties for any user.
    - Normal users may only list their own penalties.
    """
    _validate_pagination(page, page_size)

    if not is_admin and caller_user_id is not None and caller_user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view penalties for this user.",
        )

    skip = (page - 1) * page_size
    items, total = repo.list_by_user(user_id, skip=skip, limit=page_size)
    return _build_list_response(items, total, page, page_size)


def search_penalties(
    *,
    filters: Optional[PenaltySearchFilters] = None,
    page: int = 1,
    page_size: int = 50,
    is_admin: bool = False,
    repo: JSONPenaltyRepository = _repo,
) -> PenaltyListResponse:
    """
    Search penalties globally.

    - Only administrators are allowed to use this endpoint.
    - Supports filtering + pagination.
    """
    _require_admin(is_admin)
    _validate_pagination(page, page_size)

    skip = (page - 1) * page_size
    items, total = repo.search(filters=filters, skip=skip, limit=page_size)
    return _build_list_response(items, total, page, page_size)


# ------------ User Penalty Summary ------------


def get_user_penalty_summary(
    user_id: str,
    *,
    caller_user_id: Optional[str] = None,
    is_admin: bool = False,
    repo: JSONPenaltyRepository = _repo,
) -> UserPenaltySummary:
    """
    Return the summary of penalties for a user.

    - Admins may view any user's summary.
    - Normal users may only view their own summary.
    """
    if not is_admin and caller_user_id is not None and caller_user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view penalties for this user.",
        )

    return repo.get_user_summary(user_id)
