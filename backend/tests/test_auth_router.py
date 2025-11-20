from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.main import app


def test_token_success():
    client = TestClient(app)

    # user `cust1` with password `secret2` exists in backend/data/users.json
    response = client.post(
        "/auth/token", data={"username": "cust1", "password": "secret2"}
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert "access_token" in body and body["token_type"] == "bearer"


def test_me_with_valid_token():
    client = TestClient(app)
    r = client.post("/auth/token", data={"username": "cust1", "password": "secret2"})
    assert r.status_code == 200
    token = r.json()["access_token"]

    r2 = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 200
    body = r2.json()
    assert body.get("username") == "cust1"


def test_token_failure():
    client = TestClient(app)
    response = client.post(
        "/auth/token", data={"username": "cust1", "password": "wrong"}
    )
    assert response.status_code == 401


def test_admin_sync_requires_admin_token():
    client = TestClient(app)

    # Patch external sync to avoid network calls and return deterministic data
    with patch(
        "backend.services.external_sync_service.sync_external_metadata"
    ) as mock_sync:
        mock_sync.return_value = (0, datetime.now(timezone.utc))

        # No auth -> should be 401 or 403
        r = client.post("/admin/sync-external")
        assert r.status_code in (401, 403)

        # Get admin token
        r2 = client.post(
            "/auth/token", data={"username": "admin1", "password": "secret1"}
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
        "/auth/me", headers={"Authorization": "Bearer totally.invalid.token"}
    )
    assert r_invalid.status_code == 401

    # Expired token: create one with negative expiry using auth_service directly
    from backend.services import auth_service as auth_svc

    expired_token = auth_svc.create_access_token(
        {"sub": "someid", "role": "user"}, expires_delta=timedelta(seconds=-1)
    )
    r_exp = client.get("/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert r_exp.status_code == 401
