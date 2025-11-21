import unittest.mock as _mock
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


def pytest_addoption(parser):
    # placeholder to ensure pytest sees plugins/options consistently
    pass


@pytest.fixture
def mocker(request):  # noqa: C901 - complexity acceptable for test helper
    """Lightweight replacement for pytest-mock's `mocker` fixture.

    This wrapper exposes commonly used helpers from pytest-mock by
    delegating to `unittest.mock` utilities and ensuring patches are
    stopped at teardown.
    Supported helpers: `patch`, `patch.object`, `patch.dict`, `spy`,
    `mock_open`, and `patch` as a callable proxy.
    """

    class PatchProxy:
        def __init__(self, request):
            self._request = request

        def __call__(self, target, *args, **kwargs):
            p = _mock.patch(target, *args, **kwargs)
            started = p.start()
            self._request.addfinalizer(p.stop)
            return started

        def object(self, target, attribute, *args, **kwargs):
            p = _mock.patch.object(target, attribute, *args, **kwargs)
            started = p.start()
            self._request.addfinalizer(p.stop)
            return started

        def dict(self, d, values, **kwargs):
            p = _mock.patch.dict(d, values, **kwargs)
            # patch.dict is a context manager; start/stop not available.
            # Use it as context manager by returning the patch object and
            # letting tests use it if needed. For convenience, start it.
            try:
                started = p.start()
                self._request.addfinalizer(p.stop)
                return started
            except Exception:
                return p

    class Mocker:
        def __init__(self, request):
            self._request = request
            self.patch = PatchProxy(request)

        def patch_object(self, target, attribute, *args, **kwargs):
            return _mock.patch.object(target, attribute, *args, **kwargs)

        def spy(self, obj, attribute):
            """Create a spy (Mock that wraps the original callable) and
            patch the object attribute with it for the test duration.
            """
            original = getattr(obj, attribute)
            spy_mock = _mock.Mock(wraps=original)
            p = _mock.patch.object(obj, attribute, spy_mock)
            started = p.start()
            self._request.addfinalizer(p.stop)
            return started

        def mock_open(self, *args, **kwargs):
            return _mock.mock_open(*args, **kwargs)

        def __getattr__(self, name):
            # Delegate unknown attributes to the PatchProxy (e.g., patch.object)
            return getattr(self.patch, name)

    return Mocker(request)


@pytest.fixture
def mock_reviews_service(mocker):
    from backend.routers import reviews

    # Patch the service object used inside the router
    return mocker.patch.object(reviews, "svc", autospec=True)


@pytest.fixture
def mock_bookmarks_service(mocker):
    from backend.routers import bookmarks

    # Patch the service object used inside the bookmarks router
    return mocker.patch.object(bookmarks, "svc", autospec=True)
