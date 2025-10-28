from fastapi import APIRouter
from schemas.user import User
from services.users_service import create_user, validate_user

router = APIRouter(prefix="/users", tags=["users"])

@router.post("", response_model=User)
def create_user_route(user: User):
    return create_user(user)

@router.post("/validate", response_model=User)
def validate_user_route(user: User):
    return validate_user(user)