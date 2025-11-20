from fastapi import Header, HTTPException, status


def get_fake_user_id(x_user_id: str | None = Header(default=None)):
    if not x_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing X-User-Id"
        )
    return x_user_id


def get_fake_is_admin(x_user_role: str | None = Header(default=None)):
    return x_user_role == "admin"
