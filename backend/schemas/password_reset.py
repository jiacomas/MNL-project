from __future__ import annotations

from pydantic import BaseModel, EmailStr


class PasswordResetRequest(BaseModel):
    """User starts the flow by submitting their email."""
    email: EmailStr


class PasswordResetLinkOut(BaseModel):
    """What we show back instead of sending an email."""
    reset_link: str


class PasswordResetConfirm(BaseModel):
    """User completes the flow with token + new password."""
    token: str
    new_password: str
