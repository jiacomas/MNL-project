from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException
from services import password_reset_service as svc

from repositories.reset_tokens_repo import ResetTokenRepo
from repositories.users_repo import User, UsersRepo


@pytest.fixture
def repos(monkeypatch):
    """Provide fresh in-memory repos for each test and plug them into the service."""
    users = UsersRepo()
    tokens = ResetTokenRepo()

    # Replace the module-level singletons with our fresh ones
    monkeypatch.setattr(svc, "_users", users)
    monkeypatch.setattr(svc, "_tokens", tokens)

    return users, tokens


def _seed_user(users: UsersRepo) -> User:
    """Helper: create a single demo user with a known password."""
    user = User(
        id="u1",
        email="user@example.com",
        password_hash=svc.hash_password("Oldpass1"),
    )
    users.add_user(user)
    return user


# ---------------------------------------------------------------------------
# Happy path – full flow works as the story describes
# ---------------------------------------------------------------------------


def test_password_reset_happy_path(repos):
    users, tokens = repos
    user = _seed_user(users)

    # 1) User provides a registered email → system generates a reset token
    result = svc.request_password_reset(
        email="user@example.com",
        base_url="https://frontend.example",
    )

    # We got the right user + token
    assert result.user.id == user.id
    assert result.token.user_id == user.id

    # 2) System displays a temporary reset link (no email sending)
    assert result.reset_link.startswith("https://frontend.example/reset-password/")
    assert result.token.id in result.reset_link

    # 3) Token must be valid (not expired, not used yet)
    token_from_repo = tokens.get(result.token.id)
    assert token_from_repo is not None
    assert token_from_repo.is_used is False
    assert token_from_repo.is_expired is False

    # 4) User sets a new password that meets minimum rules (>= 8 chars, ≥ 1 digit)
    new_password = "Newpass1"
    svc.reset_password(token_id=result.token.id, new_password=new_password)

    # 5) On success: password is replaced (hashed) and token is invalidated
    updated_user = users.get_by_id(user.id)
    assert updated_user is not None

    # Old password should no longer verify
    assert not svc.verify_password("Oldpass1", updated_user.password_hash)
    # New password should verify
    assert svc.verify_password("Newpass1", updated_user.password_hash)

    used_token = tokens.get(result.token.id)
    assert used_token is not None
    assert used_token.is_used is True


# ---------------------------------------------------------------------------
# Error cases for the acceptance criteria
# ---------------------------------------------------------------------------


def test_request_with_unknown_email_raises_404(repos):
    users, _ = repos
    _seed_user(users)

    with pytest.raises(HTTPException) as exc:
        svc.request_password_reset("doesnotexist@example.com")

    assert exc.value.status_code == 404
    assert "Email not found" in exc.value.detail


def test_reset_with_invalid_token_raises_error(repos):
    _users, _tokens = repos

    with pytest.raises(HTTPException) as exc:
        svc.reset_password(token_id="not-a-real-token", new_password="Newpass1")

    assert exc.value.status_code == 400
    assert "Invalid or unknown reset token" in exc.value.detail


def test_reset_with_used_token_raises_error(repos):
    users, tokens = repos
    user = _seed_user(users)

    token = tokens.create_for_user(user.id)
    tokens.mark_used(token.id)

    with pytest.raises(HTTPException) as exc:
        svc.reset_password(token_id=token.id, new_password="Newpass1")

    assert exc.value.status_code == 400
    assert "already been used" in exc.value.detail


def test_reset_with_expired_token_raises_error(repos):
    users, tokens = repos
    user = _seed_user(users)

    token = tokens.create_for_user(user.id)
    # Force it to be in the past
    token.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)

    with pytest.raises(HTTPException) as exc:
        svc.reset_password(token_id=token.id, new_password="Newpass1")

    assert exc.value.status_code == 400
    assert "has expired" in exc.value.detail


@pytest.mark.parametrize(
    "bad_password, expected_message_substring",
    [
        ("short1", "at least 8 characters"),
        ("longpassword", "at least one digit"),
    ],
)
def test_password_must_meet_rules(repos, bad_password, expected_message_substring):
    users, tokens = repos
    user = _seed_user(users)
    token = tokens.create_for_user(user.id)

    with pytest.raises(HTTPException) as exc:
        svc.reset_password(token_id=token.id, new_password=bad_password)

    assert exc.value.status_code == 400
    assert expected_message_substring in exc.value.detail
