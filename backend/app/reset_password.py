"""
Description:
Implements backend password reset feature using FastAPI and JSON storage.
Follows Google Python Style Guide as required by course style rules.
"""

from __future__ import annotations

from datetime import datetime, timedelta, UTC
from pathlib import Path
import json
from uuid import uuid4

import bcrypt
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr

# ---------------------------------------------------------------------------
# Setup paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

USERS_FILE = str(DATA_DIR / "users.json")
RESET_TOKENS_FILE = str(DATA_DIR / "reset_tokens.json")

app = FastAPI(title="Password Reset API")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def load_json(file_path: str) -> dict:
    p = Path(file_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def save_json(file_path: str, data: dict) -> None:
    Path(file_path).write_text(json.dumps(data, indent=4), encoding="utf-8")


def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    """Verify plain password vs hashed."""
    return bcrypt.checkpw(password.encode(), hashed.encode())


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class ResetRequest(BaseModel):
    email: EmailStr


class ResetAction(BaseModel):
    token: str
    new_password: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.post("/password/request")
def request_password_reset(request: ResetRequest):
    """Create a reset token for a given email."""
    users = load_json(USERS_FILE)
    reset_tokens = load_json(RESET_TOKENS_FILE)

    user = next((u for u in users.values() if u.get("email") == request.email), None)
    if not user:
        raise HTTPException(status_code=404, detail="Email not found")

    token = str(uuid4())
    now = datetime.now(UTC)

    reset_tokens[token] = {
        "user_id": user["user_id"],
        "created_at": now.isoformat(),
        "expires_at": (now + timedelta(minutes=10)).isoformat(),
        "used": False,
    }

    save_json(RESET_TOKENS_FILE, reset_tokens)
    return {"message": "Password reset token created", "token": token}


@app.get("/password/validate/{token}")
def validate_token(token: str):
    """Validate if a token exists, unused, and not expired."""
    reset_tokens = load_json(RESET_TOKENS_FILE)

    if token not in reset_tokens:
        raise HTTPException(status_code=404, detail="Token not found")

    token_data = reset_tokens[token]

    if token_data["used"]:
        raise HTTPException(status_code=400, detail="Token already used")

    # ✅ Aware-to-aware comparison
    if datetime.fromisoformat(token_data["expires_at"]) < datetime.now(UTC):
        raise HTTPException(status_code=400, detail="Token expired")

    return {"message": "Token is valid"}


@app.post("/password/reset")
def reset_password(action: ResetAction):
    """Reset the user's password with a valid token."""
    reset_tokens = load_json(RESET_TOKENS_FILE)
    users = load_json(USERS_FILE)

    token_data = reset_tokens.get(action.token)
    if not token_data:
        raise HTTPException(status_code=404, detail="Invalid token")

    if token_data["used"]:
        raise HTTPException(status_code=400, detail="Token already used")

    # ✅ Aware-to-aware comparison
    if datetime.fromisoformat(token_data["expires_at"]) < datetime.now(UTC):
        raise HTTPException(status_code=400, detail="Token expired")

    user_id = token_data["user_id"]
    if user_id not in users:
        raise HTTPException(status_code=404, detail="User not found")

    users[user_id]["password_hash"] = hash_password(action.new_password)
    reset_tokens[action.token]["used"] = True

    save_json(USERS_FILE, users)
    save_json(RESET_TOKENS_FILE, reset_tokens)

    return {"message": "Password has been reset successfully"}
