from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from typing import Optional

from fastapi import HTTPException, status

from repositories.users_repo import User, UsersRepo
from repositories.reset_tokens_repo import ResetToken, ResetTokenRepo


# ----------------------------------------------------------------------------
# Simple password hashing helpers
# ----------------------------------------------------------------------------


def _hash_with_salt(password: str, salt: bytes) -> str:
    digest = hashlib.sha256()
    digest.update(salt)
    digest.update(password.encode("utf-8"))
    return digest.hexdigest()


def hash_password(password: str) -> str:
    """Hash password with random salt: 'salt_hex$hash_hex'."""
    salt = os.urandom(16)
    salt_hex = salt.hex()
    hash_hex = _hash_with_salt(password, salt)
    return f"{salt_hex}${hash_hex}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, hash_hex = stored.split("$", 1)
    except ValueError:
        return False
    salt = bytes.fromhex(salt_hex)
    candidate = _hash_with_salt(password, salt)
    return candidate == hash_hex


# ----------------------------------------------------------------------------
# Repositories (for now, module-level singletons are fine)
# ----------------------------------------------------------------------------

_users = UsersRepo()
_tokens = ResetTokenRepo()


@dataclass
class PasswordResetRequestResult:
    user: User
    token: ResetToken
    reset_link: str


def _validate_new_password(password: str) -> None:
    """Minimum rules: ≥ 8 chars, at least one digit."""
    if len(password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long.",
        )

    if not any(ch.isdigit() for ch in password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one digit.",
        )


# ----------------------------------------------------------------------------
# 1) User provides registered email → generate token.
# 2) Instead of email, we return a temporary reset link.
# ----------------------------------------------------------------------------


def request_password_reset(email: str, base_url: str = "https://example.com") -> PasswordResetRequestResult:
    user = _users.get_by_email(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email not found.",
        )

    token = _tokens.create_for_user(user.id)
    reset_link = f"{base_url.rstrip('/')}/reset-password/{token.id}"
    return PasswordResetRequestResult(user=user, token=token, reset_link=reset_link)


# ----------------------------------------------------------------------------
# 3) Token must be valid, not expired, not used.
# 4) User sets new password meeting rules.
# 5) On success old password is replaced (hashed) and token invalidated.
# ----------------------------------------------------------------------------


def reset_password(token_id: str, new_password: str) -> None:
    token = _tokens.get(token_id)
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or unknown reset token.",
        )

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

    _validate_new_password(new_password)

    user: Optional[User] = _users.get_by_id(token.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token refers to unknown user.",
        )

    # Replace password hash
    new_hash = hash_password(new_password)
    _users.update_password_hash(user.id, new_hash)

    # Invalidate the token
    _tokens.mark_used(token_id)
