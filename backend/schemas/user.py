from pydantic import BaseModel
from typing import List
from hash import Hash

class User(BaseModel):
    user_id: str
    username: str
    email: str
    password: str
    passwordHash: Hash
    is_locked: bool = False

class Admin(User):
    admin_id: str

class Customers(User):
    customer_id: str
    penalties: str
    bookmarks: List[str] = []