import hashlib
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

    def new_user_id(self) -> str:
        return uuid.uuid4().hex

    def hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    def user_exists(self, user_id: str):
        return any(user for user in self.users if user.user_id == user_id)

    def username_exists(self, username: str) -> bool:
        return any(user for user in self.users if user.username == username)

    def get_user_by_username(self, username: str) -> User | None:
        for user in self.users:
            if user.username == username:
                return user
        return None

    def check_password(self, username: str, password: str) -> bool:
        for user in self.users:
            if user.username == username and user.passwordHash == self.hash_password(
                password
            ):
                return True
        return False

    def _create_admin(
        self,
        username: str,
        email: str,
        password: str,
        admin_id: str | None = None,
        user_id: str | None = None,
        is_locked: bool = False,
    ) -> Admin:
        user_id = user_id or self.new_user_id()
        admin_id = admin_id or self.new_user_id()
        password_hash = self.hash_password(password)
        return Admin(
            user_id=user_id,
            user_type="admin",
            username=username,
            email=email,
            password=password,
            passwordHash=password_hash,
            is_locked=is_locked,
            admin_id=admin_id,
        )

    def _create_customer(
        self,
        username: str,
        email: str,
        password: str,
        customer_id: str | None = None,
        user_id: str | None = None,
        penalties: str = "",
        bookmarks: list[str] | None = None,
        is_locked: bool = False,
    ) -> Customers:
        user_id = user_id or self.new_user_id()
        customer_id = customer_id or self.new_user_id()
        password_hash = self.hash_password(password)
        return Customers(
            user_id=user_id,
            user_type="customer",
            username=username,
            email=email,
            password=password,
            passwordHash=password_hash,
            is_locked=is_locked,
            customer_id=customer_id,
            penalties=penalties,
            bookmarks=bookmarks or [],
        )

    def create_user(
        self,
        username: str,
        email: str,
        password: str,
        user_type: str,
        user_id: str | None = None,
        **kwargs,
    ) -> User:
        if self.user_exists(user_id):
            # raise ValueError("User ID already exists")
            print("User ID already exists")
        if self.username_exists(username):
            print("Username already exists")
            # raise ValueError("Username already exists")

        if user_type == "admin":
            return self._create_admin(
                username=username,
                email=email,
                password=password,
                user_id=user_id,
                **kwargs,
            )
        elif user_type == "customer":
            return self._create_customer(
                username=username,
                email=email,
                password=password,
                user_id=user_id,
                **kwargs,
            )
        else:
            raise ValueError("Invalid user type: must be 'admin' or 'customer'")

    def edit_user_info(
        self,
        username: str,
        **kwargs,
    ) -> User:
        user = self.get_user_by_username(username)
        if not user:
            raise ValueError("User not found")

        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)

        return user
