# backend/utils/datetime_utils.py
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def parse_iso_like(
    value: Any,
    *,
    default_tz: timezone = timezone.utc,
) -> datetime | None:
    """Best-effort conversion of various timestamp formats to an aware datetime.

    Supports:
    - datetime instances (adds default_tz if naive)
    - Unix timestamps (int / float)
    - ISO-8601 strings (the format we use in JSON)
    Returns None if it can't parse the value.
    """
    if value is None:
        return None

    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=default_tz)
        return value

    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=default_tz)

    if isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value)
        except ValueError:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=default_tz)
        return dt

    return None
