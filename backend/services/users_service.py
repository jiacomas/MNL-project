# create or validate a user
from schemas.user import User
from repositories.users_repo import load_all, save_all
from fastapi import HTTPException 
import uuid
from repositories.users_repo import UserRepository

def create_user(user: User):
    users = load_all()
    new_id = str(uuid.uuid4())
    if any(it.get("id") == new_id for it in users):  # extremely unlikely, but consistent check
        raise HTTPException(status_code=409, detail="ID collision; retry.")
    new_user = User(id=new_id, username=user.username, email=user.email, password=user.password)
    users.append(new_user.dict())
    save_all(users)
    return new_user

def validate_user(user: User):
    users = load_all()
    for it in users:
        if it.get("email") == user.email:
            raise HTTPException(status_code=409, detail="Email already exists")
    return True

class AuthService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    def authenticate_user(self, username: str, password: str):
        user = self.repository.find_by_username(username)
        if user is None:
            return {"error": "User not found"}
        if user.password != password:
            return {"error": "Invalid password"}
        return user