"""
Service for syncing item/movie metadata from an external API.

Enriches data/items.json with:
- poster_url
- runtime
- cast

Logs each sync in data/external_sync_log.json
with timestamp + items updated.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import Any, Tuple

import httpx

from backend import settings
from backend.repositories.movies_repo import MovieRepository
from backend.repositories.sync_repo import SyncLogRepository
from backend.schemas.movies import MovieUpdate

# Use centralized settings for external API configuration
EXTERNAL_API_BASE_URL = settings.EXTERNAL_API_BASE_URL
EXTERNAL_API_KEY_ENV = settings.EXTERNAL_API_KEY_ENV

# Repositories
_movie_repo = MovieRepository(use_json=True)
_sync_repo = SyncLogRepository()


async def _fetch_external_metadata(
    client: httpx.AsyncClient, title: str
) -> dict | None:
    api_key = os.getenv(EXTERNAL_API_KEY_ENV)
    if not api_key:
        return None

    params = {"title": title, "api_key": api_key}

    try:
        resp = await client.get(EXTERNAL_API_BASE_URL, params=params, timeout=10.0)
        resp.raise_for_status()
    except httpx.HTTPError:
        return None

    data = resp.json()

    return {
        "poster_url": data.get("poster_url") or data.get("Poster"),
        "runtime": data.get("runtime") or data.get("Runtime"),
        "cast": data.get("cast") or data.get("Actors"),
    }


async def _update_item_from_external(client: httpx.AsyncClient, item: Any) -> bool:
    title = getattr(item, "title", None)
    if not title:
        return False

    external = await _fetch_external_metadata(client, title)
    if not external:
        return False

    update_data = {}

    for key in ("poster_url", "runtime", "cast"):
        new_val = external.get(key)
        # We need to handle potential attribute error if field missing on model
        curr_val = getattr(item, key, None)

        if new_val and curr_val != new_val:
            update_data[key] = new_val
            changed = True

    if changed:
        # Perform update
        try:
            _movie_repo.update(item.movie_id, MovieUpdate(**update_data))
        except Exception:
            # If validation fails (e.g. field doesn't exist in schema), we skip
            return False

    return changed


async def sync_external_metadata() -> Tuple[int, str]:
    """
    Syncs external metadata into items.json (via MovieRepository).

    Returns:
        (items_updated_count, timestamp_str)
    """
    items, _ = _movie_repo.get_all(limit=10000)  # Get all movies

    timestamp_str = datetime.now(UTC).isoformat()
    count = 0
    updated_idxs = []

    async with httpx.AsyncClient() as client:
        for idx, item in enumerate(items):
            if await _update_item_from_external(client, item):
                count += 1
                updated_idxs.append(idx)

    # Log
    _sync_repo.append_log(
        {
            "timestamp": timestamp_str,
            "items_updated": count,
            "indices": updated_idxs,
        }
    )

    return count, timestamp_str
