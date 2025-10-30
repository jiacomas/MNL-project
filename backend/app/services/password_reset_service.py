from datetime import timedelta
from itsdangerous import BadSignature, SignatureExpired

from ..repositories.users_repo import UsersRepo
from ..repositories.reset_tokens_repo import ResetTokensRepo
from ..utils.security import (
    create_reset_token,
    decode_reset_token,
    hash_password,
    password_meets_rules,
)

RESET_EXPIRY = timedelta(minutes=30)

def _users_repo() -> UsersRepo:
    # build from current env each time (USER_DATA_PATH honored inside UsersRepo)
    return UsersRepo()

def _tokens_repo() -> ResetTokensRepo:
    # build from current env each time (SECURITY_DATA_PATH honored inside ResetTokensRepo)
    return ResetTokensRepo()


def request_reset(email: str, base_url: str = "/password/reset") -> str:
    users = _users_repo()
    tokens = _tokens_repo()

    user = users.get_by_email(email)
    if not user:
        fake = create_reset_token("unknown-user")
        return f"{base_url}?token={fake}"

    token = create_reset_token(user["user_id"])
    data = decode_reset_token(token, RESET_EXPIRY)  # safe for freshly-created token
    tokens.upsert(data["jti"], user["user_id"])
    return f"{base_url}?token={token}"


def validate_token(token: str) -> bool:
    tokens = _tokens_repo()
    try:
        data = decode_reset_token(token, RESET_EXPIRY)
    except (SignatureExpired, BadSignature):
        return False
    return not tokens.is_used(data["jti"])


def confirm_reset(token: str, new_password: str):
    """
    Returns (ok: bool, message: str|None).
    On weak password we return a specific message the test expects.
    """
    tokens = _tokens_repo()
    users = _users_repo()

    if not password_meets_rules(new_password):
        return False, "Password must be ≥8 chars and contain at least one digit"

    try:
        data = decode_reset_token(token, RESET_EXPIRY)
    except (SignatureExpired, BadSignature):
        return False, "Invalid or expired token"

    jti = data["jti"]
    if tokens.is_used(jti):
        return False, "Token already used"

    users.set_password_hash(data["sub"], hash_password(new_password))
    tokens.mark_used(jti)
    return True, None




