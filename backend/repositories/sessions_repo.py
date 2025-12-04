from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional

from backend.utils.datetime_utils import now_utc


@dataclass
class Session:
    id: str
    user_id: str
    jti: str
    token: str
    created_at: datetime
    last_active: datetime


class SessionsRepo:
    """In-memory sessions repository. Tracks active sessions by jti.

    This allows invalidating tokens on logout and enforcing inactivity timeouts.
    """

    def __init__(self) -> None:
        self._sessions: Dict[str, Session] = {}

    def create(self, user_id: str, jti: str, token: str) -> Session:
        now = now_utc()
        sess = Session(
            id=str(uuid.uuid4()),
            user_id=user_id,
            jti=jti,
            token=token,
            created_at=now,
            last_active=now,
        )
        self._sessions[jti] = sess
        return sess

    def get_by_jti(self, jti: str) -> Optional[Session]:
        return self._sessions.get(jti)

    def touch(self, jti: str) -> None:
        sess = self._sessions.get(jti)
        if sess:
            sess.last_active = now_utc()

    def delete_by_jti(self, jti: str) -> None:
        if jti in self._sessions:
            del self._sessions[jti]
