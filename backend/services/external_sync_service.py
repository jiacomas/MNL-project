"""
Service for syncing item/movie metadata from an external API.

Enriches data/movies.json with:
- poster_url
- runtime
- cast

Logs each sync in data/external_sync_log.json
with timestamp + items updated.
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, List, Tuple

import httpx

from backend import settings

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

ROOT_DATA_DIR: Path = settings.ROOT_DATA_DIR

# Tests patch MOVIES_FILE directly on this module.
# We try to use a value from settings if it exists, otherwise fall back to data/movies.json.
MOVIES_FILE: Path = Path(
    getattr(settings, "MOVIES_FILE", ROOT_DATA_DIR / "movies.json")
)

SYNC_LOG_FILE: Path = settings.SYNC_LOG_FILE
EXTERNAL_API_BASE_URL: str = settings.EXTERNAL_API_BASE_URL
EXTERNAL_API_KEY_ENV: str = settings.EXTERNAL_API_KEY_ENV


# ---------------------------------------------------------------------------
# Helper IO functions
# ---------------------------------------------------------------------------


def _load_json(path: Path) -> Any:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _save_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=4), encoding="utf-8")


# ---------------------------------------------------------------------------
# External API helpers
# ---------------------------------------------------------------------------


async def _fetch_external_metadata(
    client: httpx.AsyncClient,
    title: str,
) -> dict | None:
    """Fetch poster/runtime/cast from external API.

    Returns a normalized dict or None on error / missing API key.
    """
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


async def _update_item_from_external(client: httpx.AsyncClient, item: dict) -> bool:
    """Update a single movie dict from the external API.

    Returns True if anything actually changed.
    """
    title = item.get("title")
    if not title:
        return False

    external = await _fetch_external_metadata(client, title)
    if not external:
        return False

    changed = False
    for key in ("poster_url", "runtime", "cast"):
        value = external.get(key)
        if value and item.get(key) != value:
            item[key] = value
            changed = True

    return changed


# ---------------------------------------------------------------------------
# Public function API (used by tests + router)
# ---------------------------------------------------------------------------


async def sync_external_metadata() -> Tuple[int, str]:
    """
    Sync external metadata into movies.json.

    Returns:
        (items_updated_count, timestamp_str)
    """
    movies = _load_json(MOVIES_FILE)
    if not isinstance(movies, list):
        ts = datetime.now(UTC).isoformat()
        return 0, ts

    updated_indices: List[int] = []
    timestamp_str = datetime.now(UTC).isoformat()

    async with httpx.AsyncClient() as client:
        for idx, item in enumerate(movies):
            if await _update_item_from_external(client, item):
                updated_indices.append(idx)

    # Only write back if something actually changed
    if updated_indices:
        _save_json(MOVIES_FILE, movies)

    # Append to sync log
    log = _load_json(SYNC_LOG_FILE) or []
    if not isinstance(log, list):
        log = []

    log.append(
        {
            "timestamp": timestamp_str,
            "items_updated": len(updated_indices),
            "indices": updated_indices,
        }
    )
    _save_json(SYNC_LOG_FILE, log)

    return len(updated_indices), timestamp_str


# ---------------------------------------------------------------------------
# Backwards-compat wrapper for old tests
# ---------------------------------------------------------------------------


class ExternalSyncService:
    """Thin wrapper so tests can patch

    backend.services.external_sync_service.external_sync_service.sync_external_metadata
    """

    async def sync_external_metadata(self) -> Tuple[int, str]:
        return await sync_external_metadata()


# Object that CI tests patch against
external_sync_service = ExternalSyncService()
