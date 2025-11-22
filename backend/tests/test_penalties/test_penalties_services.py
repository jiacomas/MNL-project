# backend/tests/test_penalties/test_penalties_services.py

from datetime import datetime, timedelta, timezone
from typing import List
from unittest.mock import Mock

import pytest
from fastapi import HTTPException, status

import backend.services.penalties_services as svc
from backend.repositories.penalties_repo import JSONPenaltyRepository
from backend.schemas.penalties import (
    PenaltyCreate,
    PenaltyListResponse,
    PenaltyOut,
    PenaltySearchFilters,
    PenaltyUpdate,
    UserPenaltySummary,
)


def _future_time(days: int) -> datetime:
    """Return a UTC datetime some days in the future."""
    return datetime.now(timezone.utc) + timedelta(days=days)


def make_penalty_out(
    *,
    penalty_id: str = "p-1",
    user_id: str = "user-1",
    reason: str = "Spam",
    penalty_type: str = "temporary_ban",
    severity: int = 2,
    is_active: bool = True,
) -> PenaltyOut:
    """Convenience helper to build a PenaltyOut instance."""
    created = _future_time(1)
    updated = _future_time(2)
    return PenaltyOut(
        id=penalty_id,
        user_id=user_id,
        reason=reason,
        penalty_type=penalty_type,
        severity=severity,
        is_active=is_active,
        created_at=created,
        updated_at=updated,
        expires_at=_future_time(3),
    )


@pytest.fixture
def repo_mock() -> JSONPenaltyRepository:
    """Mocked JSONPenaltyRepository for service tests."""
    return Mock(spec=JSONPenaltyRepository)


@pytest.fixture
def sample_create_payload() -> PenaltyCreate:
    """A sample PenaltyCreate instance."""
    return PenaltyCreate(
        user_id="user-1",
        reason="Spam",
        penalty_type="temporary_ban",
        severity=2,
        expires_at=_future_time(3),
    )


@pytest.fixture
def sample_update_payload() -> PenaltyUpdate:
    """A sample PenaltyUpdate instance."""
    return PenaltyUpdate(
        reason="Updated reason",
        severity=3,
        expires_at=None,
    )


class TestCreatePenalty:
    def test_create_penalty_requires_admin(
        self, repo_mock: JSONPenaltyRepository, sample_create_payload: PenaltyCreate
    ) -> None:
        """Non-admin user cannot create penalties."""
        with pytest.raises(HTTPException) as exc:
            svc.create_penalty(
                payload=sample_create_payload,
                is_admin=False,
                repo=repo_mock,
            )

        assert exc.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Only administrators can perform this action." in exc.value.detail

    def test_create_penalty_success_for_admin(
        self, repo_mock: JSONPenaltyRepository, sample_create_payload: PenaltyCreate
    ) -> None:
        """Admin can create penalties successfully."""
        created = make_penalty_out(user_id=sample_create_payload.user_id)
        repo_mock.create.return_value = created

        result = svc.create_penalty(
            payload=sample_create_payload,
            is_admin=True,
            repo=repo_mock,
        )

        repo_mock.create.assert_called_once()
        assert isinstance(result, PenaltyOut)
        assert result.user_id == sample_create_payload.user_id
        assert result.id == created.id


class TestUpdatePenalty:
    def test_update_penalty_requires_admin(
        self, repo_mock: JSONPenaltyRepository, sample_update_payload: PenaltyUpdate
    ) -> None:
        """Non-admin user cannot update penalties."""
        with pytest.raises(HTTPException) as exc:
            svc.update_penalty(
                penalty_id="p-1",
                payload=sample_update_payload,
                is_admin=False,
                repo=repo_mock,
            )

        assert exc.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Only administrators can perform this action." in exc.value.detail

    def test_update_penalty_not_found(
        self, repo_mock: JSONPenaltyRepository, sample_update_payload: PenaltyUpdate
    ) -> None:
        """Update raises 404 when repository returns None."""
        repo_mock.update.return_value = None

        with pytest.raises(HTTPException) as exc:
            svc.update_penalty(
                penalty_id="missing-id",
                payload=sample_update_payload,
                is_admin=True,
                repo=repo_mock,
            )

        assert exc.value.status_code == status.HTTP_404_NOT_FOUND
        assert "Penalty not found" in exc.value.detail

    def test_update_penalty_success(
        self, repo_mock: JSONPenaltyRepository, sample_update_payload: PenaltyUpdate
    ) -> None:
        """Update returns updated PenaltyOut when repository succeeds."""
        updated_penalty = make_penalty_out(
            penalty_id="p-1",
            user_id="user-1",
            severity=sample_update_payload.severity or 1,
        )
        repo_mock.update.return_value = updated_penalty

        result = svc.update_penalty(
            penalty_id="p-1",
            payload=sample_update_payload,
            is_admin=True,
            repo=repo_mock,
        )

        repo_mock.update.assert_called_once_with("p-1", sample_update_payload)
        assert isinstance(result, PenaltyOut)
        assert result.id == "p-1"
        assert result.severity == sample_update_payload.severity


class TestDeletePenalty:
    def test_delete_penalty_requires_admin(
        self, repo_mock: JSONPenaltyRepository
    ) -> None:
        """Non-admin user cannot delete penalties."""
        with pytest.raises(HTTPException) as exc:
            svc.delete_penalty(
                penalty_id="p-1",
                is_admin=False,
                repo=repo_mock,
            )

        assert exc.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Only administrators can perform this action." in exc.value.detail

    def test_delete_penalty_not_found(self, repo_mock: JSONPenaltyRepository) -> None:
        """Delete raises 404 when repository returns False/None."""
        repo_mock.delete.return_value = False

        with pytest.raises(HTTPException) as exc:
            svc.delete_penalty(
                penalty_id="missing-id",
                is_admin=True,
                repo=repo_mock,
            )

        assert exc.value.status_code == status.HTTP_404_NOT_FOUND
        assert "Penalty not found" in exc.value.detail

    def test_delete_penalty_success(self, repo_mock: JSONPenaltyRepository) -> None:
        """Delete returns True when repository deletion succeeds."""
        repo_mock.delete.return_value = True

        result = svc.delete_penalty(
            penalty_id="p-1",
            is_admin=True,
            repo=repo_mock,
        )

        repo_mock.delete.assert_called_once_with("p-1")
        assert result is True


class TestDeactivatePenalty:
    def test_deactivate_penalty_requires_admin(
        self, repo_mock: JSONPenaltyRepository
    ) -> None:
        """Non-admin user cannot deactivate penalties."""
        with pytest.raises(HTTPException) as exc:
            svc.deactivate_penalty(
                penalty_id="p-1",
                is_admin=False,
                repo=repo_mock,
            )

        assert exc.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Only administrators can perform this action." in exc.value.detail

    def test_deactivate_penalty_not_found(
        self, repo_mock: JSONPenaltyRepository
    ) -> None:
        """Deactivate raises 404 when repository returns False."""
        repo_mock.deactivate.return_value = False

        with pytest.raises(HTTPException) as exc:
            svc.deactivate_penalty(
                penalty_id="missing-id",
                is_admin=True,
                repo=repo_mock,
            )

        assert exc.value.status_code == status.HTTP_404_NOT_FOUND
        assert "Penalty not found" in exc.value.detail

    def test_deactivate_penalty_success(self, repo_mock: JSONPenaltyRepository) -> None:
        """Deactivate returns True when repository succeeds."""
        repo_mock.deactivate.return_value = True

        result = svc.deactivate_penalty(
            penalty_id="p-1",
            is_admin=True,
            repo=repo_mock,
        )

        repo_mock.deactivate.assert_called_once_with("p-1")
        assert result is True


class TestGetPenalty:
    def test_get_penalty_not_found(self, repo_mock: JSONPenaltyRepository) -> None:
        """404 when penalty is not found."""
        repo_mock.get_by_id.return_value = None

        with pytest.raises(HTTPException) as exc:
            svc.get_penalty(
                penalty_id="missing-id",
                caller_user_id="user-1",
                is_admin=False,
                repo=repo_mock,
            )

        assert exc.value.status_code == status.HTTP_404_NOT_FOUND
        assert "Penalty not found" in exc.value.detail

    def test_get_penalty_as_admin(self, repo_mock: JSONPenaltyRepository) -> None:
        """Admin can retrieve any penalty."""
        penalty = make_penalty_out(user_id="some-user")
        repo_mock.get_by_id.return_value = penalty

        result = svc.get_penalty(
            penalty_id="p-1",
            caller_user_id="admin-id",
            is_admin=True,
            repo=repo_mock,
        )

        repo_mock.get_by_id.assert_called_once_with("p-1")
        assert result == penalty

    def test_get_penalty_as_owner(self, repo_mock: JSONPenaltyRepository) -> None:
        """User can retrieve their own penalty."""
        penalty = make_penalty_out(user_id="user-1")
        repo_mock.get_by_id.return_value = penalty

        result = svc.get_penalty(
            penalty_id="p-1",
            caller_user_id="user-1",
            is_admin=False,
            repo=repo_mock,
        )

        assert result == penalty

    def test_get_penalty_forbidden_for_other_user(
        self, repo_mock: JSONPenaltyRepository
    ) -> None:
        """Non-admin cannot see another user's penalty."""
        penalty = make_penalty_out(user_id="other-user")
        repo_mock.get_by_id.return_value = penalty

        with pytest.raises(HTTPException) as exc:
            svc.get_penalty(
                penalty_id="p-1",
                caller_user_id="user-1",
                is_admin=False,
                repo=repo_mock,
            )

        assert exc.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Not authorized to view this penalty." in exc.value.detail


class TestListPenaltiesForUser:
    def test_list_penalties_pagination_validation(
        self, repo_mock: JSONPenaltyRepository
    ) -> None:
        """Invalid page or page_size should raise 400 (Bad Request)."""
        # page < 1
        with pytest.raises(HTTPException) as exc:
            svc.list_penalties_for_user(
                user_id="user-1",
                caller_user_id="user-1",
                is_admin=True,
                page=0,
                page_size=10,
                repo=repo_mock,
            )
        assert exc.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Page must be greater than or equal to 1." in exc.value.detail

        # page_size < 1
        with pytest.raises(HTTPException) as exc2:
            svc.list_penalties_for_user(
                user_id="user-1",
                caller_user_id="user-1",
                is_admin=True,
                page=1,
                page_size=0,
                repo=repo_mock,
            )
        assert exc2.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Page size must be between 1 and 200." in exc2.value.detail

        # page_size too large
        with pytest.raises(HTTPException) as exc3:
            svc.list_penalties_for_user(
                user_id="user-1",
                caller_user_id="user-1",
                is_admin=True,
                page=1,
                page_size=201,
                repo=repo_mock,
            )
        assert exc3.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Page size must be between 1 and 200." in exc3.value.detail

    def test_list_penalties_forbidden_for_other_user(
        self, repo_mock: JSONPenaltyRepository
    ) -> None:
        """Non-admin cannot list penalties for another user."""
        with pytest.raises(HTTPException) as exc:
            svc.list_penalties_for_user(
                user_id="other-user",
                caller_user_id="user-1",
                is_admin=False,
                page=1,
                page_size=10,
                repo=repo_mock,
            )

        assert exc.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Not authorized to view penalties for this user." in exc.value.detail

    def test_list_penalties_for_user_success(
        self, repo_mock: JSONPenaltyRepository
    ) -> None:
        """List penalties returns a PenaltyListResponse with correct pagination."""
        penalties: List[PenaltyOut] = [
            make_penalty_out(penalty_id="p-1", user_id="user-1"),
            make_penalty_out(penalty_id="p-2", user_id="user-1"),
        ]
        repo_mock.list_by_user.return_value = (penalties, 2)

        result: PenaltyListResponse = svc.list_penalties_for_user(
            user_id="user-1",
            caller_user_id="user-1",
            is_admin=False,
            page=1,
            page_size=10,
            repo=repo_mock,
        )

        repo_mock.list_by_user.assert_called_once_with("user-1", skip=0, limit=10)
        assert isinstance(result, PenaltyListResponse)
        assert result.total == 2
        assert result.page == 1
        assert result.page_size == 10
        assert len(result.items) == 2


class TestSearchPenalties:
    def test_search_penalties_requires_admin(
        self, repo_mock: JSONPenaltyRepository
    ) -> None:
        """Non-admin cannot search penalties."""
        filters = PenaltySearchFilters()

        with pytest.raises(HTTPException) as exc:
            svc.search_penalties(
                filters=filters,
                page=1,
                page_size=10,
                is_admin=False,
                repo=repo_mock,
            )

        assert exc.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Only administrators can perform this action." in exc.value.detail

    def test_search_penalties_pagination_validation(
        self, repo_mock: JSONPenaltyRepository
    ) -> None:
        """Invalid pagination should raise 400."""
        filters = PenaltySearchFilters()

        # page < 1
        with pytest.raises(HTTPException) as exc:
            svc.search_penalties(
                filters=filters,
                page=0,
                page_size=10,
                is_admin=True,
                repo=repo_mock,
            )
        assert exc.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Page must be greater than or equal to 1." in exc.value.detail

        # page_size out of range
        with pytest.raises(HTTPException) as exc2:
            svc.search_penalties(
                filters=filters,
                page=1,
                page_size=0,
                is_admin=True,
                repo=repo_mock,
            )
        assert exc2.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Page size must be between 1 and 200." in exc2.value.detail

    def test_search_penalties_success(self, repo_mock: JSONPenaltyRepository) -> None:
        """Admin search returns a PenaltyListResponse."""
        filters = PenaltySearchFilters()
        penalties: List[PenaltyOut] = [
            make_penalty_out(penalty_id="p-1"),
            make_penalty_out(penalty_id="p-2"),
        ]
        repo_mock.search.return_value = (penalties, 2)

        result: PenaltyListResponse = svc.search_penalties(
            filters=filters,
            page=1,
            page_size=10,
            is_admin=True,
            repo=repo_mock,
        )

        repo_mock.search.assert_called_once()
        assert isinstance(result, PenaltyListResponse)
        assert result.total == 2
        assert result.page == 1
        assert result.page_size == 10
        assert len(result.items) == 2


class TestUserPenaltySummary:
    def test_get_user_penalty_summary_forbidden_for_other_user(
        self, repo_mock: JSONPenaltyRepository
    ) -> None:
        """Non-admin cannot access another user's penalty summary."""
        with pytest.raises(HTTPException) as exc:
            svc.get_user_penalty_summary(
                user_id="other-user",
                caller_user_id="user-1",
                is_admin=False,
                repo=repo_mock,
            )

        assert exc.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Not authorized to view penalties for this user." in exc.value.detail

    def test_get_user_penalty_summary_success_for_owner(
        self, repo_mock: JSONPenaltyRepository
    ) -> None:
        """User can view their own penalty summary."""
        summary = UserPenaltySummary(
            user_id="user-1",
            total_penalties=3,
            active_penalties=2,
            max_severity=4,
            has_permanent_ban=False,
        )
        repo_mock.get_user_summary.return_value = summary

        result = svc.get_user_penalty_summary(
            user_id="user-1",
            caller_user_id="user-1",
            is_admin=False,
            repo=repo_mock,
        )

        repo_mock.get_user_summary.assert_called_once_with("user-1")
        assert result == summary

    def test_get_user_penalty_summary_success_for_admin(
        self, repo_mock: JSONPenaltyRepository
    ) -> None:
        """Admin can view penalty summary for any user."""
        summary = UserPenaltySummary(
            user_id="other-user",
            total_penalties=1,
            active_penalties=1,
            max_severity=5,
            has_permanent_ban=True,
        )
        repo_mock.get_user_summary.return_value = summary

        result = svc.get_user_penalty_summary(
            user_id="other-user",
            caller_user_id="admin-id",
            is_admin=True,
            repo=repo_mock,
        )

        repo_mock.get_user_summary.assert_called_once_with("other-user")
        assert result == summary
