from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass

from fastapi import HTTPException, status

from backend.repositories.reset_tokens_repo import ResetToken, ResetTokenRepo
from backend.repositories.users_repo import User, UsersRepo  # type: ignore[import]

# -----------------------------------------------------------------------------
# Configuration / module-level repositories
# -----------------------------------------------------------------------------

# These are kept as module-level singletons so tests can monkeypatch them:
#   monkeypatch.setattr(svc, "_users", fake_users_repo)
#   monkeypatch.setattr(svc, "_tokens", fake_tokens_repo)
_users: UsersRepo = UsersRepo()
_tokens: ResetTokenRepo = ResetTokenRepo()


# -----------------------------------------------------------------------------
# Models
# -----------------------------------------------------------------------------


@dataclass
class PasswordResetRequestResult:
    """Return type for a successful password reset request."""

    user: User
    token: ResetToken
    reset_link: str


# -----------------------------------------------------------------------------
# Password hashing helpers
# -----------------------------------------------------------------------------


def _hash_with_salt(password: str, salt: bytes) -> str:
    """Return a SHA-256 hex digest of `salt + password`."""
    digest = hashlib.sha256()
    digest.update(salt)
    digest.update(password.encode("utf-8"))
    return digest.hexdigest()


def hash_password(password: str) -> str:
    """Hash a password using a random salt.

    Stored format:
        "<salt_hex>$<hash_hex>"
    """
    salt = os.urandom(16)
    salt_hex = salt.hex()
    hash_hex = _hash_with_salt(password, salt)
    return f"{salt_hex}${hash_hex}"


def _legacy_hash(password: str) -> str:
    """Legacy hashing format: plain SHA-256(password).hexdigest()."""
    digest = hashlib.sha256()
    digest.update(password.encode("utf-8"))
    return digest.hexdigest()


def verify_password(password: str, stored: str) -> bool:
    """Verify a password against either:

    * New format: "<salt_hex>$<hash_hex>"
    * Legacy format: plain SHA-256 hex digest
    """
    try:
        salt_hex, hash_hex = stored.split("$", 1)
    except ValueError:
        # Legacy format – no salt present, treat `stored` as SHA-256(password).
        return _legacy_hash(password) == stored

    salt = bytes.fromhex(salt_hex)
    candidate = _hash_with_salt(password, salt)
    return candidate == hash_hex


# -----------------------------------------------------------------------------
# Password rules
# -----------------------------------------------------------------------------

_MIN_PASSWORD_LENGTH = 8


def _validate_new_password(password: str) -> None:
    """Enforce password rules; raise HTTP 400 on failure.

    Rules (messages must match tests exactly):
    * At least 8 characters
    * At least one digit
    """
    if len(password) < _MIN_PASSWORD_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long.",
        )

    if not any(ch.isdigit() for ch in password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one digit.",
        )


# -----------------------------------------------------------------------------
# Internal helpers for repos / tokens
# -----------------------------------------------------------------------------


def _get_user_by_email_or_404(email: str) -> User:
    """Look up a user by email or raise HTTP 404."""
    user = _users.get_by_email(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email not found.",
        )
    return user


def _get_token_or_error(token_id: str) -> ResetToken:
    """Fetch token by id or raise HTTP 400 with the correct message."""
    token = _tokens.get(token_id)
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or unknown reset token.",
        )
    return token


def _ensure_token_usable(token: ResetToken) -> None:
    """Raise HTTP 400 if token is used or expired (messages match tests)."""
    if token.is_used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has already been used.",
        )

    if token.is_expired:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired.",
        )


# -----------------------------------------------------------------------------
# Public API: request / perform password reset
# -----------------------------------------------------------------------------


def request_password_reset(
    email: str,
    base_url: str = "https://example.com",
) -> PasswordResetRequestResult:
    """Create a password reset token and return the reset link.

    The caller is responsible for sending the link via email.
    """
    user = _get_user_by_email_or_404(email)

    # Create token bound to this user
    token = _tokens.create_for_user(user.user_id)

    # Ensure we don't double-slash if base_url already ends with '/'
    reset_link = f"{base_url.rstrip('/')}/reset-password/{token.id}"

    return PasswordResetRequestResult(
        user=user,
        token=token,
        reset_link=reset_link,
    )


def reset_password(token_id: str, new_password: str) -> None:
    """Reset a user's password using a one-time reset token."""
    # 1. Lookup token and validate state
    token = _get_token_or_error(token_id)
    _ensure_token_usable(token)

    # 2. Validate new password against policy
    _validate_new_password(new_password)

    # 3. Load user referenced by token
    user = _users.get_by_id(token.user_id)
    if user is None:
        # Shouldn't normally happen, but we guard against it explicitly.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token refers to unknown user.",
        )

    # 4. Update password hash and persist via repo
    new_hash = hash_password(new_password)
    _users.update_password_hash(user.user_id, new_hash)

    # 5. Mark token as used so it cannot be reused
    _tokens.mark_used(token_id)
