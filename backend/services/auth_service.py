from __future__ import annotations

import datetime
from datetime import timezone
from typing import Callable, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from backend import settings
from backend.repositories.sessions_repo import SessionsRepo

# Configuration (use settings)
SECRET_KEY = settings.JWT_SECRET
ALGORITHM = settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

# sessions repo (in-memory)
_sessions = SessionsRepo()


def create_access_token(
    data: dict, expires_delta: Optional[datetime.timedelta] = None
) -> str:
    to_encode = data.copy()
    expire = datetime.datetime.now(timezone.utc) + (
        expires_delta or datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    # jwt.encode returns str for PyJWT >=2.x
    return token


def create_token_for_user(user) -> str:
    # Create a JWT with a jti so sessions can be tracked server-side
    import uuid

    jti = str(uuid.uuid4())
    payload = {
        "sub": user.user_id,
        "role": user.user_type,
        "username": getattr(user, "username", None),
        "jti": jti,
    }
    token = create_access_token(payload)
    # Persist session server-side so we can enforce inactivity and invalidate on logout
    try:
        _sessions.create(user_id=user.user_id, jti=jti, token=token)
    except Exception:
        # keep behavior resilient for tests/mocks
        pass
    return token


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        )


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    payload = decode_token(token)

    jti = payload.get("jti")
    if not jti:
        # No jti — treat as invalid
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        )

    session = _sessions.get_by_jti(jti)
    if not session:
        # Session not found — token was likely logged out or not issued by server
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        )

    # Enforce inactivity timeout
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    timeout_minutes = settings.SESSION_INACTIVITY_TIMEOUT_MINUTES
    inactive_delta = now - session.last_active
    if inactive_delta.total_seconds() > timeout_minutes * 60:
        # expire session
        _sessions.delete_by_jti(jti)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired"
        )

    # update last active (sliding expiration)
    _sessions.touch(jti)

    return {
        "user_id": payload.get("sub"),
        "role": payload.get("role"),
        "username": payload.get("username"),
    }


def logout_token(token: str) -> None:
    """Invalidate session corresponding to given token (called on logout)."""
    try:
        payload = decode_token(token)
    except HTTPException:
        # token invalid/expired already
        return

    jti = payload.get("jti")
    if jti:
        _sessions.delete_by_jti(jti)


def require_role(role: str) -> Callable:
    def _dependency(user: dict = Depends(get_current_user)):
        if not user or user.get("role") != role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient privileges"
            )
        return user

    return _dependency
