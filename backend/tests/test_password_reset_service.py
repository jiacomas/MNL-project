from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException

from backend.repositories.reset_tokens_repo import ResetTokenRepo
from backend.repositories.users_repo import User, UserRepository
from backend.services import password_reset_service as svc


@pytest.fixture
def repos(mocker):
    """
    Provide fresh in-memory repos for each test and plug them into the service.

    We create new UserRepository and ResetTokenRepo instances, then patch the
    module-level _users and _tokens singletons in password_reset_service so
    every test is isolated and does not touch real disk state.
    """
    users = UserRepository()
    tokens = ResetTokenRepo()

    # Replace module-level singletons in the service with our fresh repos
    mocker.patch.object(svc, "_users", users)
    mocker.patch.object(svc, "_tokens", tokens)

    return users, tokens


def _seed_user(users: UserRepository) -> User:
    """
    Create a demo user that matches the current User schema and add it to the repo.
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


def test_password_reset_happy_path(repos):
    users, tokens = repos
    user = _seed_user(users)

    # 1) Request a reset token
    result = svc.request_password_reset(
        email="user@example.com",
        base_url="https://frontend.example",
    )

    # Returned result is consistent and linked to the same user
    assert result.user.user_id == user.user_id
    assert result.token.user_id == user.user_id
    assert result.reset_link.startswith("https://frontend.example/reset-password/")
    assert result.token.id in result.reset_link

    # Token is stored in repo and is not used/expired
    token_from_repo = tokens.get(result.token.id)
    assert token_from_repo is not None
    assert token_from_repo.is_used is False
    assert token_from_repo.is_expired is False

    # 2) Reset password using the token
    svc.reset_password(token_id=result.token.id, new_password="Newpass1")

    updated_user = users.get_by_id(user.user_id)
    assert updated_user is not None

    # Old password must fail, new password must verify
    assert not svc.verify_password("Oldpass1", updated_user.passwordHash)
    assert svc.verify_password("Newpass1", updated_user.passwordHash)

    # Token is now marked as used
    used_token = tokens.get(result.token.id)
    assert used_token.is_used is True


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------


def test_request_with_unknown_email_raises_404(repos):
    users, _ = repos
    _seed_user(users)

    with pytest.raises(HTTPException) as exc:
        svc.request_password_reset("doesnotexist@example.com")

    assert exc.value.status_code == 404
    assert "Email not found" in exc.value.detail


def test_reset_with_invalid_token_raises_error(repos):
    # repos fixture still wires up fresh in-memory repos
    _users, _tokens = repos  # noqa: F841  (kept for clarity)

    with pytest.raises(HTTPException) as exc:
        svc.reset_password(token_id="not-a-real-token", new_password="Newpass1")

    assert exc.value.status_code == 400
    assert "Invalid or unknown reset token" in exc.value.detail


def test_reset_with_used_token_raises_error(repos):
    users, tokens = repos
    user = _seed_user(users)

    token = tokens.create_for_user(user.user_id)
    tokens.mark_used(token.id)

    with pytest.raises(HTTPException) as exc:
        svc.reset_password(token_id=token.id, new_password="Newpass1")

    assert exc.value.status_code == 400
    assert "already been used" in exc.value.detail


def test_reset_with_expired_token_raises_error(repos):
    users, tokens = repos
    user = _seed_user(users)

    token = tokens.create_for_user(user.user_id)
    # Manually expire token
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
    token = tokens.create_for_user(user.user_id)

    with pytest.raises(HTTPException) as exc:
        svc.reset_password(token_id=token.id, new_password=bad_password)

    assert exc.value.status_code == 400
    assert expected_message_substring in exc.value.detail
