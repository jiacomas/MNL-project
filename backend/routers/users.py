"""User management router for admin operations and auth endpoints."""

import re

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm

import backend.services.auth_service as auth_svc
from backend.deps import get_current_user_id
from backend.repositories.users_repo import UserRepository
from backend.schemas.users import UserCreate
from backend.services.auth_service import get_current_user, require_role
from backend.services.export_service import generate_user_export
from backend.services.users_service import UsersService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("")
def list_users(admin=Depends(require_role("admin"))):
    """
    List all users in the system (admin only).
    Returns sanitized user data without password hashes.
    """
    repo = UserRepository()
    users = repo.users

    # Sanitize user data - remove sensitive fields
    sanitized_users = []
    for user in users:
        user_dict = user.model_dump()
        # Remove sensitive fields
        user_dict.pop("password", None)
        user_dict.pop("passwordHash", None)
        sanitized_users.append(user_dict)

    return {"users": sanitized_users}


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_user(body: dict):
    """Create a new user (public endpoint used by tests)."""
    repo = UserRepository()
    svc = UsersService(repo)

    username = body.get("username")
    email = body.get("email")
    password = body.get("password")
    if not username or not email or not password:
        raise HTTPException(status_code=400, detail="Missing fields")

    user = svc.create_user(
        username, email, password, user_type=body.get("user_type", "customer")
    )
    if user is None:
        raise HTTPException(status_code=400, detail="Could not create user")
    return user.model_dump()


def _validate_password(password: str) -> bool:
    """Basic password validation: at least 6 chars, contains a letter and a number."""
    if not password or len(password) < 6:
        return False
    if not re.search(r"[A-Za-z]", password):
        return False
    if not re.search(r"[0-9]", password):
        return False
    return True


@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(body: UserCreate):
    """Public signup endpoint for customers.

    Creates a new customer with a generated id, `penalties` set to "0",
    empty `bookmarks`, a hashed `passwordHash`, and `is_locked=False`.
    Returns the created user without sensitive fields.
    """
    repo = UserRepository()
    svc = UsersService(repo)

    username = body.username
    email = body.email
    password = body.password

    if repo.username_exists(username):
        raise HTTPException(status_code=400, detail="Username already exists")

    if not _validate_password(password):
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 6 characters and include letters and numbers",
        )

    user = svc.create_user(
        username,
        email,
        password,
        user_type="customer",
        penalties="0",
        bookmarks=[],
        is_locked=False,
    )

    if user is None:
        raise HTTPException(status_code=400, detail="Could not create user")

    user_dict = user.model_dump()
    user_dict.pop("password", None)
    user_dict.pop("passwordHash", None)
    return user_dict


@router.post("/token")
def token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticate user and return JWT access token."""
    repo = UserRepository()
    svc = UsersService(repo)
    token = svc.authenticate_user(form_data.username, form_data.password)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me")
def me(user: dict = Depends(get_current_user)):
    """Return the current authenticated user info (lightweight)."""
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or missing token")
    return user


@router.get("/me/export")
def export_me(user_id: str = Depends(get_current_user_id)):
    """Return an export of the user's data as JSON with attachment headers."""
    payload = generate_user_export(user_id)
    filename = f"user_export_{user_id}.json"
    return JSONResponse(
        content=payload,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/logout")
def logout(token: str = Depends(auth_svc.oauth2_scheme)):
    """Invalidate the current token (logout)."""
    auth_svc.logout_token(token)
    return {"status": "logged_out"}
