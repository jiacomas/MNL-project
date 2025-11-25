from __future__ import annotations

from datetime import timedelta
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend import settings
from backend.main import app
from backend.services import auth_service as auth_svc
from backend.services.users_service import UsersService


# In-memory fake repository to avoid filesystem access in tests
class FakeUserRepository:
    def __init__(self):
        self.users = []
        self.file_path = ""

    def new_user_id(self) -> str:
        import uuid

        return uuid.uuid4().hex

    def save(self) -> None:
        # no-op: do not write to disk in tests
        return

    def user_exists(self, user_id: str):
        return any(user for user in self.users if user.user_id == user_id)

    def username_exists(self, username: str) -> bool:
        return any(user for user in self.users if user.username == username)

    def get_user_by_username(self, username: str):
        for user in self.users:
            if user.username == username:
                return user
        return None

    def add_user(self, user) -> None:
        self.users.append(user)

    def get_by_id(self, user_id: str):
        for user in self.users:
            if user.user_id == user_id:
                return user
        return None


fake_repo = FakeUserRepository()


def ensure_user(username: str = "cust1", password: str = "secret2") -> None:
    svc = UsersService(fake_repo)
    if not fake_repo.get_user_by_username(username):
        svc.create_user(
            username, f"{username}@example.com", password, user_type="customer"
        )


def test_logout_invalidates_token():
    ensure_user()

    # Patch repository references used by the app routes to use our in-memory repo
    with (
        patch("backend.repositories.users_repo.UserRepository", new=lambda: fake_repo),
        patch("backend.routers.auth.UserRepository", new=lambda: fake_repo),
    ):
        client = TestClient(app)

        r = client.post(
            "/auth/token", data={"username": "cust1", "password": "secret2"}
        )
        assert r.status_code == 200
        token = r.json()["access_token"]

        # token should work initially
        r2 = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert r2.status_code == 200

        # logout
        r3 = client.post("/auth/logout", headers={"Authorization": f"Bearer {token}"})
        assert r3.status_code == 200

        # subsequent requests should be unauthorized
        r4 = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert r4.status_code == 401


def test_inactivity_timeout_expires_session():
    ensure_user()

    with (
        patch("backend.repositories.users_repo.UserRepository", new=lambda: fake_repo),
        patch("backend.routers.auth.UserRepository", new=lambda: fake_repo),
    ):
        client = TestClient(app)

        r = client.post(
            "/auth/token", data={"username": "cust1", "password": "secret2"}
        )
        assert r.status_code == 200
        token = r.json()["access_token"]

        # decode token to get jti and session
        payload = auth_svc.decode_token(token)
        jti = payload.get("jti")
        assert jti is not None

        sess = auth_svc._sessions.get_by_jti(jti)
        assert sess is not None

        # simulate inactivity by rewinding last_active beyond timeout
        timeout = settings.SESSION_INACTIVITY_TIMEOUT_MINUTES
        sess.last_active = sess.last_active - timedelta(minutes=timeout + 1)

        # request should now be considered expired
        r2 = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert r2.status_code == 401
        assert r2.json().get("detail") == "Session expired"
