from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional


@dataclass
class ResetToken:
    id: str
    user_id: str
    expires_at: datetime
    used_at: Optional[datetime] = None

    @property
    def is_used(self) -> bool:
        return self.used_at is not None

    @property
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) >= self.expires_at


class ResetTokenRepo:
    """In-memory token repo. Swap for DB/CSV later if needed."""

    def __init__(self) -> None:
        self._tokens: Dict[str, ResetToken] = {}

    def create_for_user(self, user_id: str, lifetime_minutes: int = 15) -> ResetToken:
        token_id = str(uuid.uuid4())
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=lifetime_minutes)
        token = ResetToken(id=token_id, user_id=user_id, expires_at=expires_at)
        self._tokens[token_id] = token
        return token

    def get(self, token_id: str) -> Optional[ResetToken]:
        return self._tokens.get(token_id)

    def mark_used(self, token_id: str) -> None:
        token = self._tokens[token_id]
        token.used_at = datetime.now(timezone.utc)
