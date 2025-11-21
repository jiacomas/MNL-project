from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Tuple

import pytest
from fastapi import HTTPException

from backend.repositories.reset_tokens_repo import ResetTokenRepo
from backend.repositories.users_repo import User, UserRepository
from backend.services import password_reset_service as svc

# ---------------------------------------------------------------------------
# Fixtures & helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def repos(monkeypatch) -> Tuple[UserRepository, ResetTokenRepo]:
    """
    Provide fresh in-memory repos for each test and plug them into
    the password_reset_service module-level singletons.
    """
    users = UserRepository()
    tokens = ResetTokenRepo()

    # Replace module-level singletons used by the service
    monkeypatch.setattr(svc, "_users", users)
    monkeypatch.setattr(svc, "_tokens", tokens)

    return users, tokens


def _seed_user(users: UserRepository) -> User:
    """
    Create and persist a demo user that matches the current User schema.
    """
    user = User(
        user_id="u1",
        user_type="customer",
        username="demo",
        email="user@example.com",
        password="Oldpass1",
        passwordHash=svc.hash_password("Oldpass1"),
        is_locked=False,
    )
    users.add_user(user)
    return user


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


def test_password_reset_happy_path(repos) -> None:
    users, tokens = repos
    user = _seed_user(users)

    # 1) User requests a reset token
    result = svc.request_password_reset(
        email="user@example.com",
        base_url="https://frontend.example",
    )

    # Verify linkage between user and token
    assert result.user.user_id == user.user_id
    assert result.token.user_id == user.user_id
    assert result.reset_link.startswith("https://frontend.example/reset-password/")
    assert result.token.id in result.reset_link

    # Token must be stored and valid
    token_from_repo = tokens.get(result.token.id)
    assert token_from_repo is not None
    assert token_from_repo.is_used is False
    assert token_from_repo.is_expired is False

    # 2) Reset password with the token
    svc.reset_password(token_id=result.token.id, new_password="Newpass1")

    # User's password hash should be updated
    updated_user = users.get_by_id(user.user_id)
    assert updated_user is not None
    assert not svc.verify_password("Oldpass1", updated_user.passwordHash)
    assert svc.verify_password("Newpass1", updated_user.passwordHash)

    # Token should now be marked as used
    used_token = tokens.get(result.token.id)
    assert used_token is not None
    assert used_token.is_used is True


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------


def test_request_with_unknown_email_raises_404(repos) -> None:
    users, _ = repos
    _seed_user(users)

    with pytest.raises(HTTPException) as exc:
        svc.request_password_reset("doesnotexist@example.com")

    assert exc.value.status_code == 404
    assert "Email not found" in exc.value.detail


def test_reset_with_invalid_token_raises_error(repos) -> None:
    # repos fixture still sets up _users/_tokens, but we don't need them directly here
    _, _ = repos  # explicit to show we're using the fixture

    with pytest.raises(HTTPException) as exc:
        svc.reset_password(token_id="not-a-real-token", new_password="Newpass1")

    assert exc.value.status_code == 400
    assert "Invalid or unknown reset token" in exc.value.detail


def test_reset_with_used_token_raises_error(repos) -> None:
    users, tokens = repos
    user = _seed_user(users)

    token = tokens.create_for_user(user.user_id)
    tokens.mark_used(token.id)

    with pytest.raises(HTTPException) as exc:
        svc.reset_password(token_id=token.id, new_password="Newpass1")

    assert exc.value.status_code == 400
    assert "already been used" in exc.value.detail


def test_reset_with_expired_token_raises_error(repos) -> None:
    users, tokens = repos
    user = _seed_user(users)

    token = tokens.create_for_user(user.user_id)
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
def test_password_must_meet_rules(
    repos,
    bad_password: str,
    expected_message_substring: str,
) -> None:
    users, tokens = repos
    user = _seed_user(users)
    token = tokens.create_for_user(user.user_id)

    with pytest.raises(HTTPException) as exc:
        svc.reset_password(token_id=token.id, new_password=bad_password)

    assert exc.value.status_code == 400
    assert expected_message_substring in exc.value.detail
