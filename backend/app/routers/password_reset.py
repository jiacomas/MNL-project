# backend/app/routers/password_reset.py
from fastapi import APIRouter, HTTPException
from ..schemas.auth import (
    PasswordResetRequest,
    PasswordResetConfirm,
    PasswordResetValidateResponse,
    PasswordResetRequestResponse,
)
from ..services import password_reset_service as svc

router = APIRouter(prefix="/password", tags=["password"])

@router.post("/request", response_model=PasswordResetRequestResponse)
def request_password_reset(payload: PasswordResetRequest):
    link = svc.request_reset(email=payload.email, base_url="/password/reset")
    return PasswordResetRequestResponse(reset_link=link)

@router.get("/validate/{token}", response_model=PasswordResetValidateResponse)
def validate_password_token(token: str):
    ok = svc.validate_token(token)
    if not ok:
        raise HTTPException(status_code=400, detail="Invalid or used token")
    return PasswordResetValidateResponse(valid=True)

@router.post("/reset")
def confirm_password_reset(payload: PasswordResetConfirm):
    ok, msg = svc.confirm_reset(token=payload.token, new_password=payload.new_password)
    if not ok:
        raise HTTPException(status_code=400, detail=msg or "Invalid token or password does not meet rules")
    return {"message": "Password updated."}



