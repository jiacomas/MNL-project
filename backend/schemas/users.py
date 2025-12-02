from typing import List

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


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
