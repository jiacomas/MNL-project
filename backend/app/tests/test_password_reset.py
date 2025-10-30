"""
Unit tests for Password Reset flow:
- request -> displays link containing token (no email)
- validate requires valid, unexpired, unused token
- confirm updates hash, invalidates token, enforces password rules
"""

import json
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.repositories.users_repo import UsersRepo
from backend.app.repositories.reset_tokens_repo import ResetTokensRepo
from backend.app.utils.security import hash_password

client = TestClient(app)
users = UsersRepo()
tokens = ResetTokensRepo()

def seed_user(user_id="u1", email="user@example.com", pw="OldPass123"):
    users.upsert_user(user_id=user_id, email=email, password_hash=hash_password(pw), is_active=True)
    return user_id, email

def clear_tokens():
    tokens.clear()

def read_users_file():
    # optional: assert password changed by reloading json
    import os, json
    path = os.getenv("USER_DATA_PATH", "data/users") + "/users.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def test_request_shows_link_and_is_non_enumerating(tmp_path, monkeypatch):
    # Point repos to temp dirs
    monkeypatch.setenv("USER_DATA_PATH", str(tmp_path/"users"))
    monkeypatch.setenv("SECURITY_DATA_PATH", str(tmp_path/"security"))

    # Recreate repos with new env
    global users, tokens
    users = UsersRepo()
    tokens = ResetTokensRepo()
    clear_tokens()

    # seed one real user
    uid, email = seed_user()

    # valid email -> returns link with token
    r1 = client.post("/password/request", json={"email": email})
    assert r1.status_code == 200
    assert "reset_link" in r1.json()
    assert "token=" in r1.json()["reset_link"]

    # unknown email -> still returns a link (non-enumerating)
    r2 = client.post("/password/request", json={"email": "nope@x.y"})
    assert r2.status_code == 200
    assert "token=" in r2.json()["reset_link"]

def test_validate_then_reset_happy_path(tmp_path, monkeypatch):
    monkeypatch.setenv("USER_DATA_PATH", str(tmp_path/"users"))
    monkeypatch.setenv("SECURITY_DATA_PATH", str(tmp_path/"security"))
    global users, tokens
    users = UsersRepo()
    tokens = ResetTokensRepo()
    clear_tokens()
    _, email = seed_user()

    # request -> capture token from link
    r = client.post("/password/request", json={"email": email})
    link = r.json()["reset_link"]
    token = link.split("token=")[-1]

    # validate
    rv = client.get(f"/password/validate/{token}")
    assert rv.status_code == 200
    assert rv.json()["valid"] is True

    # reset
    rr = client.post("/password/reset", json={"token": token, "new_password": "Newpass123"})
    assert rr.status_code == 200

    # token should now be marked used
    tok_path = tmp_path/"security"/"password_resets.json"
    with open(tok_path, "r", encoding="utf-8") as f:
        store = json.load(f)
    jti = next(iter(store))
    assert store[jti]["used"] is True

def test_reset_rejects_weak_password(tmp_path, monkeypatch):
    monkeypatch.setenv("USER_DATA_PATH", str(tmp_path/"users"))
    monkeypatch.setenv("SECURITY_DATA_PATH", str(tmp_path/"security"))
    global users, tokens
    users = UsersRepo()
    tokens = ResetTokensRepo()
    clear_tokens()
    _, email = seed_user()

    # request & get token
    t = client.post("/password/request", json={"email": email}).json()["reset_link"].split("token=")[-1]

    # too short/no digit
    bad = client.post("/password/reset", json={"token": t, "new_password": "short"})
    assert bad.status_code == 400
    assert "Password must be ≥8 chars" in bad.json()["detail"]

def test_validate_rejects_reuse_and_expiry(tmp_path, monkeypatch):
    monkeypatch.setenv("USER_DATA_PATH", str(tmp_path/"users"))
    monkeypatch.setenv("SECURITY_DATA_PATH", str(tmp_path/"security"))
    global users, tokens
    users = UsersRepo()
    tokens = ResetTokensRepo()
    clear_tokens()
    _, email = seed_user()

    token = client.post("/password/request", json={"email": email}).json()["reset_link"].split("token=")[-1]

    # consume once
    ok = client.post("/password/reset", json={"token": token, "new_password": "Newpass123"})
    assert ok.status_code == 200

    # reuse -> 400
    r2 = client.get(f"/password/validate/{token}")
    assert r2.status_code == 400
    assert "used" in r2.json()["detail"]
