from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class User:
    id: str
    email: str
    password_hash: str


class UsersRepo:
    """Simple in-memory user store.

    In a real project it needs to be hook up to the DB instead.
    """

    def __init__(self) -> None:
        self._by_id: Dict[str, User] = {}
        self._by_email: Dict[str, User] = {}

    # ------------------------------------------------------------------
    # Helper used in tests / seeding
    # ------------------------------------------------------------------
    def add_user(self, user: User) -> None:
        self._by_id[user.id] = user
        self._by_email[user.email.lower()] = user

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def get_by_email(self, email: str) -> Optional[User]:
        return self._by_email.get(email.lower())

    def get_by_id(self, user_id: str) -> Optional[User]:
        return self._by_id.get(user_id)

    def update_password_hash(self, user_id: str, new_hash: str) -> None:
        user = self._by_id[user_id]
        user.password_hash = new_hash
