from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.main import app
from backend.repositories.users_repo import UserRepository
from backend.services.users_service import UsersService


def test_create_user_success():
    client = TestClient(app)
    # Use a unique username to avoid conflicts with other tests
    username = f"newuser_{datetime.now().timestamp()}"
    response = client.post(
        "/users/",
        json={
            "username": username,
            "email": f"{username}@example.com",
            "password": "password123",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == username
    assert "user_id" in data


def test_token_success():
    client = TestClient(app)

    # Ensure test user exists (some test runs modify users.json)
    repo = UserRepository()
    svc = UsersService(repo)
    if not repo.get_user_by_username("cust1"):
        svc.create_user("cust1", "cust1@example.com", "secret2", user_type="customer")

    response = client.post(
        "/users/token", data={"username": "cust1", "password": "secret2"}
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert "access_token" in body and body["token_type"] == "bearer"


def test_me_with_valid_token():
    client = TestClient(app)
    # Ensure user exists
    repo = UserRepository()
    svc = UsersService(repo)
    if not repo.get_user_by_username("cust1"):
        svc.create_user("cust1", "cust1@example.com", "secret2", user_type="customer")

    r = client.post("/users/token", data={"username": "cust1", "password": "secret2"})
    assert r.status_code == 200
    token = r.json()["access_token"]

    r2 = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 200
    body = r2.json()
    assert body.get("username") == "cust1"


def test_export_data():
    client = TestClient(app)
    repo = UserRepository()
    svc = UsersService(repo)
    if not repo.get_user_by_username("cust1"):
        svc.create_user("cust1", "cust1@example.com", "secret2", user_type="customer")

    # Login
    r = client.post("/users/token", data={"username": "cust1", "password": "secret2"})
    token = r.json()["access_token"]

    # Export
    r2 = client.get("/users/me/export", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 200
    assert r2.headers["content-type"] == "application/json"
    assert "attachment" in r2.headers["content-disposition"]

    data = r2.json()
    assert "meta" in data
    assert "data" in data
    assert data["meta"]["user_id"] is not None
    assert isinstance(data["data"]["reviews"], list)
    assert isinstance(data["data"]["bookmarks"], list)
    assert isinstance(data["data"]["history"], list)


def test_token_failure():
    client = TestClient(app)
    response = client.post(
        "/users/token", data={"username": "cust1", "password": "wrong"}
    )
    assert response.status_code == 401


def test_admin_sync_requires_admin_token():
    client = TestClient(app)

    # Patch external sync to avoid network calls and return deterministic data
    with patch(
        "backend.services.external_sync_service.external_sync_service.sync_external_metadata"
    ) as mock_sync:
        mock_sync.return_value = (0, datetime.now(timezone.utc))

        # No auth -> should be 401 or 403
        r = client.post("/admin/sync-external")
        assert r.status_code in (401, 403)

        # Ensure admin exists and get admin token
        repo = UserRepository()
        svc = UsersService(repo)
        if not repo.get_user_by_username("admin1"):
            svc.create_user(
                "admin1", "admin1@example.com", "secret1", user_type="admin"
            )

        r2 = client.post(
            "/users/token", data={"username": "admin1", "password": "secret1"}
        )
        assert r2.status_code == 200
        token = r2.json()["access_token"]

        # Call with admin token
        r3 = client.post(
            "/admin/sync-external", headers={"Authorization": f"Bearer {token}"}
        )
        assert r3.status_code == 200


def test_me_with_invalid_and_expired_tokens():
    client = TestClient(app)

    # Invalid token (random string)
    r_invalid = client.get(
        "/users/me", headers={"Authorization": "Bearer totally.invalid.token"}
    )
    assert r_invalid.status_code == 401

    # Expired token: create one with negative expiry using auth_service directly
    from backend.services import auth_service as auth_svc

    expired_token = auth_svc.create_access_token(
        {"sub": "someid", "role": "user"}, expires_delta=timedelta(seconds=-1)
    )
    r_exp = client.get(
        "/users/me", headers={"Authorization": f"Bearer {expired_token}"}
    )
    assert r_exp.status_code == 401
