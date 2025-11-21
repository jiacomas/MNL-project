import warnings
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.repositories.users_repo import UserRepository
from backend.services import auth_service
from backend.services.users_service import UsersService


# ---- Test client (shared) ----
@pytest.fixture(scope="session")
def client():
    return TestClient(app)


# ---- Timestamp helper (global, not fixture) ----
def now_iso():
    return datetime.now(timezone.utc).isoformat()


# ---- JWT headers ----
@pytest.fixture
def jwt_user_headers():
    token = auth_service.create_access_token(
        {"sub": "u1", "role": "user", "username": "u1"},
        expires_delta=timedelta(minutes=30),
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def jwt_admin_headers():
    token = auth_service.create_access_token(
        {"sub": "admin", "role": "admin", "username": "admin"},
        expires_delta=timedelta(minutes=30),
    )
    return {"Authorization": f"Bearer {token}"}


# ---- Token factory (for integration tests needing dynamic users) ----
@pytest.fixture(scope="session")
def token_factory():
    def _make(username: str, role: str = "user"):
        repo = UserRepository()
        service = UsersService(repo)

        if not repo.get_user_by_username(username):
            service.create_user(
                username=username,
                email=f"{username}@example.com",
                password="password123",
                user_type=role,
            )

        user = repo.get_user_by_username(username)
        return auth_service.create_access_token(
            {"sub": user.user_id, "role": role, "username": username},
            expires_delta=timedelta(minutes=30),
        )

    return _make


# ---- Ignore python-jose deprecated utcnow warning ----
def pytest_configure(config):
    warnings.filterwarnings(
        "ignore",
        category=DeprecationWarning,
        message=r".*utcnow\(\) is deprecated.*",
        module=r"jose\.jwt",
    )


@pytest.fixture
def mock_reviews_service(mocker):
    from backend.routers import reviews

    # Patch the service object used inside the router
    return mocker.patch.object(reviews, "svc", autospec=True)
