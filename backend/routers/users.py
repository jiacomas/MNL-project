from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm

from backend.repositories.users_repo import UserRepository
from backend.schemas.users import User, UserCreate
from backend.services import auth_service as auth_svc
from backend.services import export_service
from backend.services.users_service import UsersService

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
def create_user(user_create: UserCreate):
    """Create a new user (registration)."""
    repo = UserRepository()
    svc = UsersService(repo)

    new_user = svc.create_user(
        username=user_create.username,
        email=user_create.email,
        password=user_create.password,
        user_type="customer",  # Default to customer for public registration
    )

    if not new_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or ID already exists",
        )

    return new_user


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


@router.get("/me/export")
def export_data(user: dict = Depends(auth_svc.get_current_user)):
    """
    Download all user data (reviews, bookmarks, history) as a JSON file.
    """
    user_id = user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid user session")

    data = export_service.generate_user_export(user_id)

    filename = f"user_export_{data['meta']['generated_at'].replace(':', '-')}.json"

    return JSONResponse(
        content=data,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.post("/logout")
def logout(token: str = Depends(auth_svc.oauth2_scheme)) -> dict:
    """Logout by invalidating the current session/token."""
    auth_svc.logout_token(token)
    return {"message": "Logged out"}
