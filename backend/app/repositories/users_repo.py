from __future__ import annotations
import json, os
from typing import Optional, Dict

BASE_PATH = os.getenv("USER_DATA_PATH", "data/users")
USERS_JSON = os.path.join(BASE_PATH, "users.json")

def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def _load() -> Dict[str, dict]:
    if not os.path.exists(USERS_JSON):
        return {}
    with open(USERS_JSON, "r", encoding="utf-8") as f:
        return json.load(f)

def _save(data: Dict[str, dict]) -> None:
    _ensure_dir(BASE_PATH)
    tmp = USERS_JSON + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, USERS_JSON)

class UsersRepo:
    """
    JSON users:
    {
      "u1": {"email": "a@b.com", "password_hash": "...", "is_active": true}
    }
    """

    def get_by_email(self, email: str) -> Optional[dict]:
        db = _load()
        for uid, u in db.items():
            if u.get("email") == email:
                return {"user_id": uid, **u}
        return None

    def set_password_hash(self, user_id: str, new_hash: str) -> None:
        db = _load()
        if user_id not in db:
            raise KeyError("User not found")
        db[user_id]["password_hash"] = new_hash
        _save(db)

    # Helpers for tests/seed
    def upsert_user(self, user_id: str, email: str, password_hash: str, is_active: bool=True) -> None:
        db = _load()
        db[user_id] = {"email": email, "password_hash": password_hash, "is_active": is_active}
        _save(db)
