from datetime import datetime, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.deps import require_admin
from backend.routers.penalties import get_auth_context, router
from backend.schemas.penalties import (
    PenaltyListResponse,
    PenaltyOut,
    UserPenaltySummary,
)

# ---------- FastAPI app & client fixtures ----------


@pytest.fixture
def app():
    """
    Create a FastAPI app instance and include the penalties' router.
    Override auth-related dependencies so that tests do not depend on real JWTs.
    """
    app = FastAPI()
    app.include_router(router)

    # Always act as an admin user in tests that depend on require_admin
    app.dependency_overrides[require_admin] = lambda: {
        "user_id": "admin-user",
        "role": "admin",
    }

    # For endpoints that use get_auth_context, behave as an admin as well
    app.dependency_overrides[get_auth_context] = lambda: {
        "user_id": "admin-user",
        "is_admin": True,
    }

    return app


@pytest.fixture
def client(app):
    """
    Provide a TestClient bound to the FastAPI app.
    """
    return TestClient(app)


# ---------- Tests for create penalty endpoint ----------


class TestCreatePenaltyRouter:
    def test_create_penalty_calls_service_and_returns_penalty(
        self, client, monkeypatch
    ):
        """
        Ensure that:
        - The router calls penalties_services.create_penalty with correct arguments.
        - A PenaltyOut object returned by the service is serialized correctly.
        - The HTTP status code is 201 Created.
        """
        from backend.services import penalties_services

        called = {}

        def fake_create_penalty(*, payload, is_admin: bool):
            called["payload"] = payload
            called["is_admin"] = is_admin

            now = datetime.now(timezone.utc)
            return PenaltyOut(
                id="pen_1",
                penalty_type=payload.penalty_type,
                user_id=payload.user_id,
                reason=payload.reason,
                severity=payload.severity,
                created_at=now,
                updated_at=now,
                is_active=True,
            )

        monkeypatch.setattr(
            penalties_services,
            "create_penalty",
            fake_create_penalty,
        )

        # Use a penalty_type that does not require expires_at to avoid validation issues
        request_body = {
            "penalty_type": "review_restriction",
            "user_id": "user_1",
            "reason": "Test reason",
            "severity": 3,
        }

        response = client.post("/penalties/", json=request_body)

        assert response.status_code == 201
        data = response.json()

        # Basic response structure checks
        assert data["id"] == "pen_1"
        assert data["user_id"] == "user_1"
        assert data["penalty_type"] == "review_restriction"
        assert data["reason"] == "Test reason"

        # Ensure service was called with admin privileges
        assert called["is_admin"] is True
        assert called["payload"].user_id == "user_1"
        assert called["payload"].reason == "Test reason"


# ---------- Tests for delete penalty endpoint ----------


class TestDeletePenaltyRouter:
    def test_delete_penalty_calls_service_and_returns_no_content(
        self, client, monkeypatch
    ):
        """
        Ensure delete endpoint:
        - Calls penalties_services.delete_penalty with correct ID and admin flag.
        - Returns 204 No Content.
        """
        from backend.services import penalties_services

        called = {}

        def fake_delete_penalty(penalty_id: str, *, is_admin: bool) -> bool:
            called["penalty_id"] = penalty_id
            called["is_admin"] = is_admin
            return True

        monkeypatch.setattr(
            penalties_services,
            "delete_penalty",
            fake_delete_penalty,
        )

        response = client.delete("/penalties/pen_123")

        assert response.status_code == 204
        # Body should be empty for 204
        assert response.content in (b"",)


# ---------- Tests for deactivate penalty endpoint ----------


class TestDeactivatePenaltyRouter:
    def test_deactivate_penalty_calls_service(self, client, monkeypatch):
        """
        Ensure deactivate endpoint:
        - Calls penalties_services.deactivate_penalty with correct ID and admin flag.
        - Returns 204 No Content.
        """
        from backend.services import penalties_services

        called = {}

        def fake_deactivate_penalty(penalty_id: str, *, is_admin: bool) -> bool:
            called["penalty_id"] = penalty_id
            called["is_admin"] = is_admin
            return True

        monkeypatch.setattr(
            penalties_services,
            "deactivate_penalty",
            fake_deactivate_penalty,
        )

        response = client.post("/penalties/pen_999/deactivate")

        assert response.status_code == 204
        assert called["penalty_id"] == "pen_999"
        assert called["is_admin"] is True


# ---------- Tests for get single penalty endpoint ----------


class TestGetPenaltyRouter:
    def test_get_penalty_calls_service_and_returns_penalty(self, client, monkeypatch):
        """
        Ensure get endpoint:
        - Calls penalties_services.get_penalty with correct arguments.
        - Returns the PenaltyOut object provided by the service.
        """
        from backend.services import penalties_services

        called = {}

        def fake_get_penalty(
            penalty_id: str,
            *,
            caller_user_id: str,
            is_admin: bool,
        ) -> PenaltyOut:
            called["penalty_id"] = penalty_id
            called["caller_user_id"] = caller_user_id
            called["is_admin"] = is_admin

            now = datetime.now(timezone.utc)
            return PenaltyOut(
                id=penalty_id,
                penalty_type="temporary_ban",
                user_id="target_user",
                reason="Some reason",
                severity=2,
                created_at=now,
                updated_at=now,
                is_active=True,
            )

        monkeypatch.setattr(
            penalties_services,
            "get_penalty",
            fake_get_penalty,
        )

        response = client.get("/penalties/pen_abc")

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == "pen_abc"
        assert data["user_id"] == "target_user"
        assert data["penalty_type"] == "temporary_ban"

        # Ensure service was called with correct auth context
        assert called["penalty_id"] == "pen_abc"
        assert called["caller_user_id"] == "admin-user"
        assert called["is_admin"] is True


# ---------- Tests for search penalties endpoint ----------


class TestSearchPenaltiesRouter:
    def test_search_penalties_returns_list_response(self, client, monkeypatch):
        """
        Ensure search endpoint:
        - Builds PenaltySearchFilters correctly.
        - Passes pagination and is_admin flag to service.
        - Returns a PenaltyListResponse instance as JSON.
        """
        from backend.services import penalties_services

        called = {}

        def fake_search_penalties(
            *,
            filters,
            page: int,
            page_size: int,
            is_admin: bool,
        ) -> PenaltyListResponse:
            called["filters"] = filters
            called["page"] = page
            called["page_size"] = page_size
            called["is_admin"] = is_admin

            now = datetime.now(timezone.utc)
            penalty = PenaltyOut(
                id="pen_1",
                penalty_type="review_restriction",
                user_id="user_x",
                reason="Test search penalty",
                severity=1,
                created_at=now,
                updated_at=now,
                is_active=True,
            )

            return PenaltyListResponse(
                items=[penalty],
                total=1,
                page=page,
                page_size=page_size,
                total_pages=1,
            )

        monkeypatch.setattr(
            penalties_services,
            "search_penalties",
            fake_search_penalties,
        )

        params = {
            "user_id": "user_x",
            "penalty_type": "review_restriction",
            "severity": 1,
            "is_active": True,
            "page": 2,
            "page_size": 5,
        }

        response = client.get("/penalties/search", params=params)

        assert response.status_code == 200
        data = response.json()

        # Basic structure checks
        assert data["total"] == 1
        assert data["page"] == 2
        assert data["page_size"] == 5
        assert data["total_pages"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["user_id"] == "user_x"

        # Ensure service was called with correct filters and flags
        filters = called["filters"]
        assert filters.user_id == "user_x"
        assert filters.penalty_type == "review_restriction"
        assert filters.severity == 1
        assert filters.is_active is True
        assert called["page"] == 2
        assert called["page_size"] == 5
        assert called["is_admin"] is True


# ---------- Tests for user penalty summary endpoint ----------


class TestUserPenaltySummaryRouter:
    def test_get_user_penalty_summary_returns_summary(self, client, monkeypatch):
        """
        Ensure summary endpoint:
        - Calls penalties_services.get_user_penalty_summary with correct arguments.
        - Returns a UserPenaltySummary payload from the service.
        """
        from backend.services import penalties_services

        called = {}

        def fake_get_user_penalty_summary(
            user_id: str,
            *,
            caller_user_id: str,
            is_admin: bool,
        ) -> UserPenaltySummary:
            called["user_id"] = user_id
            called["caller_user_id"] = caller_user_id
            called["is_admin"] = is_admin

            return UserPenaltySummary(
                user_id=user_id,
                total_penalties=3,
                active_penalties=1,
                max_severity=4,
                has_permanent_ban=False,
            )

        monkeypatch.setattr(
            penalties_services,
            "get_user_penalty_summary",
            fake_get_user_penalty_summary,
        )

        response = client.get("/penalties/users/user_123/summary")

        assert response.status_code == 200
        data = response.json()

        assert data["user_id"] == "user_123"
        assert data["total_penalties"] == 3
        assert data["active_penalties"] == 1
        assert data["max_severity"] == 4
        assert data["has_permanent_ban"] is False

        # Ensure service was called with correct auth context
        assert called["user_id"] == "user_123"
        assert called["caller_user_id"] == "admin-user"
        assert called["is_admin"] is True
