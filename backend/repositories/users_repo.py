import json
import os
import uuid
from typing import Any, List

from backend.schemas.users import Admin, Customers, User

DATA_PATH = "backend/data/users.json"


def load_all(path: str = DATA_PATH) -> List[User]:
    """Load users.json into User/Pydantic objects."""
    if not os.path.exists(path):
        return []

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    users: List[User] = []
    for item in data:
        user_type = item.get("user_type")
        if user_type == "admin":
            users.append(Admin(**item))
        elif user_type == "customer":
            users.append(Customers(**item))
        else:
            raise ValueError(f"Unknown user type: {user_type}")

    return users


def save_all(items: List[Any], path: str = DATA_PATH) -> None:
    """Serialize list of users (Pydantic models) into JSON."""
    dirpath = os.path.dirname(path)
    if dirpath:
        os.makedirs(dirpath, exist_ok=True)

    def _to_serializable(obj):
        if obj is None:
            return None
        if isinstance(obj, (str, int, float, bool)):
            return obj
        if isinstance(obj, dict):
            return {k: _to_serializable(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_to_serializable(v) for v in obj]
        # Pydantic model
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        # Generic object
        if hasattr(obj, "__dict__"):
            return {
                k: _to_serializable(v)
                for k, v in obj.__dict__.items()
                if not k.startswith("_")
            }
        return str(obj)

    serializable = [_to_serializable(item) for item in items]

    with open(path, "w", encoding="utf-8") as f:
        json.dump(serializable, f, ensure_ascii=False, indent=2)


class UserRepository:
    """Primary user repository used throughout backend code."""

    def __init__(self, file_path: str = DATA_PATH):
        self.file_path = file_path
        self.users = load_all(file_path)

    # ------------------------------------------------------------
    # Creation + persistence
    # ------------------------------------------------------------

    def new_user_id(self) -> str:
        return uuid.uuid4().hex

    def save(self) -> None:
        save_all(self.users, path=self.file_path)

    # ------------------------------------------------------------
    # Lookups
    # ------------------------------------------------------------

    def user_exists(self, user_id: str) -> bool:
        return any(u.user_id == user_id for u in self.users)

    def username_exists(self, username: str) -> bool:
        return any(u.username == username for u in self.users)

    def get_user_by_username(self, username: str) -> User | None:
        return next((u for u in self.users if u.username == username), None)

    def get_by_id(self, user_id: str) -> User | None:
        return next((u for u in self.users if u.user_id == user_id), None)

    def get_by_email(self, email: str) -> User | None:
        return next((u for u in self.users if u.email == email), None)

    # ------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------

    def add_user(self, user: User) -> None:
        """Append new user and persist."""
        self.users.append(user)
        self.save()

    def update_password_hash(self, user_id: str, new_hash: str) -> None:
        for user in self.users:
            if user.user_id == user_id:
                user.passwordHash = new_hash
                self.save()
                return


# -------------------------------------------------------------------
# BACKWARD COMPATIBILITY (IMPORTANT!)
#
# Some older code still imports:
#     from backend.repositories.users_repo import UsersRepo
#
# To avoid import errors (like the one you hit), we alias it.
# -------------------------------------------------------------------
UsersRepo = UserRepository
