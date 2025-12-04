"""
User management router for admin operations.
"""

from fastapi import APIRouter, Depends

from backend.repositories.users_repo import UserRepository
from backend.services.auth_service import require_role

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
