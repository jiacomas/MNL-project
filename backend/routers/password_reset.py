from __future__ import annotations

from fastapi import APIRouter

from schemas.password_reset import (
    PasswordResetRequest,
    PasswordResetLinkOut,
    PasswordResetConfirm,
)
from services import password_reset_service as svc

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/request-reset", response_model=PasswordResetLinkOut)
def request_reset(body: PasswordResetRequest) -> PasswordResetLinkOut:
    """User submits email → we generate token and show a link."""
    result = svc.request_password_reset(email=body.email)
    # Acceptance criteria: instead of sending email, display reset link.
    return PasswordResetLinkOut(reset_link=result.reset_link)


@router.post("/reset-password")
def reset_password(body: PasswordResetConfirm) -> dict[str, str]:
    """User submits token + new password to complete the reset."""
    svc.reset_password(token_id=body.token, new_password=body.new_password)
    return {"status": "password_reset_success"}
