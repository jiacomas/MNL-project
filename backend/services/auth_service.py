from __future__ import annotations

import datetime
import os
from typing import Callable, Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET", "dev-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def create_access_token(
    data: dict, expires_delta: Optional[datetime.timedelta] = None
) -> str:
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + (
        expires_delta or datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    # jwt.encode returns str for PyJWT >=2.x
    return token


def create_token_for_user(user) -> str:
    payload = {
        "sub": user.user_id,
        "role": user.user_type,
        "username": getattr(user, "username", None),
    }
    return create_access_token(payload)


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired"
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    payload = decode_token(token)
    return {
        "user_id": payload.get("sub"),
        "role": payload.get("role"),
        "username": payload.get("username"),
    }


def require_role(role: str) -> Callable:
    def _dependency(user: dict = Depends(get_current_user)):
        if not user or user.get("role") != role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient privileges"
            )
        return user

    return _dependency
