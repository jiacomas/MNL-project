"""
Unit tests for Password Reset API.
Covers token validation and password reset behavior (timezone-safe version).
"""

import json
from datetime import datetime, timedelta, UTC
from fastapi.testclient import TestClient
import pytest
from app import reset_password as main
import backend.app.reset_password as main


client = TestClient(main.app)


# ---------------------------------------------------------------------------
# Setup Helpers
# ---------------------------------------------------------------------------
def setup_users():
    users = {
        "u1": {
            "user_id": "u1",
            "email": "test@example.com",
            "username": "user1",
            "password_hash": main.hash_password("OldPass123"),
        }
    }
    with open(main.USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=4)
    return users


def clear_tokens():
    with open(main.RESET_TOKENS_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
def test_validate_token_decision_table_unit(monkeypatch):
    """
    Unit test: validate_token() via Decision Table.
    Uses timezone-aware datetime (UTC) for token timestamps.
    """

    valid_token = "t_valid"
    expired_token = "t_expired"
    used_token = "t_used"

    now = datetime.now(UTC)

    tokens = {
        valid_token: {
            "user_id": "u1",
            "created_at": now.isoformat(),
            "expires_at": (now + timedelta(minutes=10)).isoformat(),
            "used": False,
        },
        expired_token: {
            "user_id": "u1",
            "created_at": now.isoformat(),
            "expires_at": (now - timedelta(minutes=1)).isoformat(),
            "used": False,
        },
        used_token: {
            "user_id": "u1",
            "created_at": now.isoformat(),
            "expires_at": (now + timedelta(minutes=10)).isoformat(),
            "used": True,
        },
    }

    monkeypatch.setattr(main, "load_json", lambda path: tokens)

    # R1: Valid token
    r1 = main.validate_token(valid_token)
    assert r1 == {"message": "Token is valid"}

    # R2: Expired token 
    with pytest.raises(main.HTTPException) as e2:
        main.validate_token(expired_token)
    assert e2.value.status_code == 400
    assert "expired" in e2.value.detail.lower()

    # R3: Used token 
    with pytest.raises(main.HTTPException) as e3:
        main.validate_token(used_token)
    assert e3.value.status_code == 400
    assert "used" in e3.value.detail.lower()

    # R4: Missing token 
    with pytest.raises(main.HTTPException) as e4:
        main.validate_token("t_missing")
    assert e4.value.status_code == 404


def test_request_then_reset_password_integration(tmp_path, monkeypatch):
    """Integration test: full flow using temporary JSON files."""
    users_file = tmp_path / "users.json"
    tokens_file = tmp_path / "reset_tokens.json"

    monkeypatch.setattr(main, "USERS_FILE", str(users_file))
    monkeypatch.setattr(main, "RESET_TOKENS_FILE", str(tokens_file))

    users = {
        "u1": {
            "user_id": "u1",
            "email": "test@example.com",
            "username": "user1",
            "password_hash": main.hash_password("OldPass123"),
        }
    }
    users_file.write_text(json.dumps(users), encoding="utf-8")

    client = TestClient(main.app)

    # Step 1: request reset token
    r_req = client.post("/password/request", json={"email": "test@example.com"})
    assert r_req.status_code == 200
    token = r_req.json()["token"]

    # Step 2: validate token
    r_val = client.get(f"/password/validate/{token}")
    assert r_val.status_code == 200

    # Step 3: reset password
    r_reset = client.post(
        "/password/reset",
        json={"token": token, "new_password": "NewPassword123"},
    )
    assert r_reset.status_code == 200

    tokens = json.loads(tokens_file.read_text(encoding="utf-8"))
    assert tokens[token]["used"] is True
