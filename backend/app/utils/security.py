import os
import re
import uuid
from datetime import timedelta
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from passlib.context import CryptContext

APP_SECRET = os.getenv("APP_SECRET", "change-me-in-prod")
RESET_SALT = "password-reset"
_serializer = URLSafeTimedSerializer(APP_SECRET)
_pwd = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto", pbkdf2_sha256__rounds=29000)

def hash_password(plain: str) -> str:
    return _pwd.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    return _pwd.verify(plain, hashed)

def create_reset_token(subject: str, jti: str | None = None) -> str:
    if not jti:
        jti = str(uuid.uuid4())
    payload = {"sub": subject, "jti": jti, "purpose": "password_reset"}
    return _serializer.dumps(payload, salt=RESET_SALT)

def decode_reset_token(token: str, max_age: timedelta) -> dict:
    data = _serializer.loads(token, salt=RESET_SALT, max_age=int(max_age.total_seconds()))
    if data.get("purpose") != "password_reset":
        raise BadSignature("Invalid purpose")
    return data

_password_rule = re.compile(r".*\d")  # at least one digit

def password_meets_rules(pw: str) -> bool:
    return len(pw) >= 8 and any(c.isdigit() for c in pw)
