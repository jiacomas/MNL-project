from fastapi import Depends, HTTPException, status

from backend.services.auth_service import get_current_user


def get_current_user_id(user: dict = Depends(get_current_user)):
    if not user or "user_id" not in user:
        raise HTTPException(status_code=401, detail="Invalid or missing token")
    return user["user_id"]


def require_admin(user: dict = Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    return user
