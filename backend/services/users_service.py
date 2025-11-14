import hashlib
import uuid
from typing import Any, Optional

from backend.repositories.users_repo import UserRepository
from backend.schemas.users import Admin, Customers, User


class UsersService:
    """Service layer for user-related operations.

    Responsibilities moved here from the repository:
    - create_user
    - hash_password
    - check_password

    The service persists changes using the provided UserRepository instance.
    """

    def __init__(self, repo: UserRepository):
        self.repo = repo

    def hash_password(self, password: str) -> str:
        """Return a SHA-256 hex digest for the given password."""
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    def check_password(self, username: str, password: str) -> bool:
        """Verify that the provided password matches the stored password hash.

        Returns True for match, False otherwise.
        """
        user = self.repo.get_user_by_username(username)
        if not user:
            return False
        stored = getattr(user, "passwordHash", None)
        if not stored:
            return False
        return stored == self.hash_password(password)

    def create_user(
        self,
        username: str,
        email: str,
        password: str,
        user_type: str,
        user_id: Optional[str] = None,
        **kwargs: Any,
    ) -> User:
        """Create and persist a new Admin or Customer user.

        - Validates username uniqueness.
        - Generates ids when not provided.
        - Persists to the repository's data file.
        """
        if user_id and self.repo.user_exists(user_id):
            raise ValueError("User ID already exists")
            # print("User ID already exists")
        if self.repo.username_exists(username):
            raise ValueError("Username already exists")
            # print("Username already exists")

        user_id = user_id or uuid.uuid4().hex

        password_hash = self.hash_password(password)

        if user_type == "admin":
            admin_id = kwargs.get("admin_id") or uuid.uuid4().hex
            user = Admin(
                user_id=user_id,
                user_type="admin",
                username=username,
                email=email,
                password=password,
                passwordHash=password_hash,
                is_locked=kwargs.get("is_locked", False),
                admin_id=admin_id,
            )
        elif user_type == "customer":
            customer_id = kwargs.get("customer_id") or uuid.uuid4().hex
            user = Customers(
                user_id=user_id,
                user_type="customer",
                username=username,
                email=email,
                password=password,
                passwordHash=password_hash,
                is_locked=kwargs.get("is_locked", False),
                customer_id=customer_id,
                penalties=kwargs.get("penalties", ""),
                bookmarks=kwargs.get("bookmarks", []) or [],
            )
        else:
            raise ValueError("Invalid user type: must be 'admin' or 'customer'")

        # append and persist
        self.repo.save()
        return user

    def edit_user_info(self, username: str, **kwargs: Any) -> User:
        """Update user fields and persist changes."""
        user = self.repo.get_user_by_username(username)
        if not user:
            raise ValueError("User not found")
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        self.repo.save()
        return user
