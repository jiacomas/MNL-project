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


def now_utc() -> datetime:
    """Get current UTC time as timezone-aware datetime.

    Use this instead of datetime.now(timezone.utc) for consistency.
    Makes testing easier by providing a single point to mock.
    """
    return datetime.now(timezone.utc)


def to_iso_string(dt: datetime | None) -> str | None:
    """Convert datetime to ISO-8601 string for JSON serialization.

    Returns None if input is None.
    Ensures the datetime is timezone-aware before conversion.
    """
    if dt is None:
        return None

    # Ensure timezone-aware
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt.isoformat()


def ensure_timezone_aware(
    dt: datetime | None,
    tz: timezone = timezone.utc,
) -> datetime | None:
    """Ensure a datetime is timezone-aware.

    If the datetime is naive, adds the specified timezone.
    If already aware, returns unchanged.
    Returns None if input is None.
    """
    if dt is None:
        return None

    if dt.tzinfo is None:
        return dt.replace(tzinfo=tz)

    return dt


def format_timestamp(dt: datetime | None = None) -> str:
    """Format a datetime as a timestamp string for filenames.

    Format: YYYYMMDD_HHMMSS
    If dt is None, uses current UTC time.

    Example: "20231204_143022"
    """
    if dt is None:
        dt = now_utc()

    # Ensure timezone-aware
    dt = ensure_timezone_aware(dt)

    return dt.strftime("%Y%m%d_%H%M%S")
