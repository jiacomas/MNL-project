from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from backend.repositories.users_repo import UserRepository
from backend.services import auth_service as auth_svc
from backend.services.users_service import UsersService

router = APIRouter(prefix="/auth", tags=["auth"])


# Simple token endpoint that returns a Bearer token when credentials are valid.
@router.post("/token")
def token(form_data: OAuth2PasswordRequestForm = Depends()):
    repo = UserRepository()
    svc = UsersService(repo)

    token = svc.authenticate_user(form_data.username, form_data.password)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {"access_token": token, "token_type": "bearer"}


@router.get("/me")
def me(user: dict = Depends(auth_svc.get_current_user)) -> dict:
    """Return current authenticated user information (from JWT)."""
    return user
