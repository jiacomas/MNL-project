# create or validate a user
# from fastapi import HTTPException
from backend.repositories.users_repo import UserRepository


class AuthService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    def authenticate_user(self, username: str, password: str):
        user = self.repository.username_exists(username)
        if user is None:
            return {"error": "User not found"}
        if not self.repository.check_password(username, password):
            return {"error": "Invalid password"}
        return user
