import json
import os
import uuid
from typing import Any, Dict, List

from backend.schemas.users import Admin, Customers, User

DATA_PATH = "backend/data/users.json"


def load_all(path: str = DATA_PATH) -> List[User]:
    users = []
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        for item in data:
            if item.get("user_type") == "admin":
                users.append(Admin(**item))
            elif item.get("user_type") == "customer":
                users.append(Customers(**item))
            else:
                raise ValueError(f"Unknown user type: {item.get('user_type')}")
    return users


def save_all(items: List[Dict[str, Any]], path: str = DATA_PATH) -> None:
    # ensure directory exists
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
        # pydantic models / dataclasses / objects with dict-like API
        if hasattr(obj, "dict") and callable(getattr(obj, "dict")):
            return _to_serializable(obj.dict())
        if hasattr(obj, "to_dict") and callable(getattr(obj, "to_dict")):
            return _to_serializable(obj.to_dict())
        if hasattr(obj, "__dict__"):
            return _to_serializable(
                {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}
            )
        # fallback to string representation
        return str(obj)

    serializable_items = [_to_serializable(item) for item in items]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(serializable_items, f, ensure_ascii=False, indent=2)


class UserRepository:
    def __init__(self, file_path: str = DATA_PATH):
        self.users = load_all(file_path)
        # remember where this repository loads/saves data so services can persist
        self.file_path = file_path

    def new_user_id(self) -> str:
        return uuid.uuid4().hex

    def save(self) -> None:
        """Persist current users list to the configured data file."""
        save_all(self.users, path=self.file_path)

    def user_exists(self, user_id: str):
        return any(user for user in self.users if user.user_id == user_id)

    def username_exists(self, username: str) -> bool:
        return any(user for user in self.users if user.username == username)

    def get_user_by_username(self, username: str) -> User | None:
        for user in self.users:
            if user.username == username:
                return user
        return None

    def add_user(self, user: User) -> None:
        """Add a new user instance."""
        self.users.append(user)
        self.save()

    def get_by_id(self, user_id: str) -> User | None:
        """Retrieve a user by user_id."""
        for user in self.users:
            if user.user_id == user_id:
                return user
        return None

    def get_by_email(self, email: str) -> User | None:
        for user in self.users:
            if user.email == email:
                return user
        return None

    def update_password_hash(self, user_id: str, new_hash: str) -> None:
        for user in self.users:
            if user.user_id == user_id:
                user.passwordHash = new_hash
                self.save()
                return
