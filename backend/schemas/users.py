from typing import List

from pydantic import BaseModel


class User(BaseModel):
    user_id: str
    user_type: str
    username: str
    email: str
    password: str
    passwordHash: str
    is_locked: bool = False


class Admin(User):
    admin_id: str


class Customers(User):
    customer_id: str | None = None
    penalties: str = ""
    bookmarks: List[str] = []
