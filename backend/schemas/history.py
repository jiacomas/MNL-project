from __future__ import annotations

from pydantic import BaseModel


class HistoryEntryOut(BaseModel):
    """API representation of a single viewing-history entry.

    `title` and `release_year` are optional so the backend can
    start with movie_id + timestamp only, and later be enriched
    with metadata if needed.
    """

    movie_id: str
    last_viewed_at: str  # ISO-8601 timestamp string
    title: str | None = None
    release_year: int | None = None
