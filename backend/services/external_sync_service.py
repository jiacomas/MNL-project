from __future__ import annotations

"""
Service for syncing movie metadata (poster, runtime, cast) from an external API.

- Reads / writes movies.json
- Enriches existing movies (no duplicates)
- Logs each sync with timestamp and indices updated
"""

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

import httpx

from backend import settings

JsonObj = Dict[str, Any]

# ---------------------------------------------------------------------------
# Configuration (kept here so tests can patch/override easily)
# ---------------------------------------------------------------------------

ROOT_DATA_DIR: Path = getattr(settings, "ROOT_DATA_DIR", Path("data"))

MOVIES_FILE: Path = getattr(
    settings,
    "MOVIES_FILE",
    ROOT_DATA_DIR / "movies.json",
)

SYNC_LOG_FILE: Path = getattr(
    settings,
    "SYNC_LOG_FILE",
    ROOT_DATA_DIR / "external_sync_log.json",
)

EXTERNAL_API_BASE_URL: str = getattr(
    settings,
    "EXTERNAL_API_BASE_URL",
    "https://www.omdbapi.com/",
)

# Name of the env var that stores the API key
EXTERNAL_API_KEY_ENV: str = getattr(
    settings,
    "EXTERNAL_API_KEY_ENV",
    "OMDB_API_KEY",
)


# ---------------------------------------------------------------------------
# Basic JSON helpers
# ---------------------------------------------------------------------------


def _load_json(path: Path) -> Any:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def _save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=4), encoding="utf-8")


# ---------------------------------------------------------------------------
# External API helpers
# ---------------------------------------------------------------------------


async def _fetch_external_metadata(
    client: httpx.AsyncClient,
    title: str,
) -> JsonObj | None:
    """Call the external API for a single title.

    Returns a small dict with keys poster_url, runtime, cast or None on error.
    """
    api_key = os.getenv(EXTERNAL_API_KEY_ENV)
    if not api_key:
        # No key configured -> skip external calls quietly
        return None

    # These params match OMDb style APIs but can be adjusted to your provider
    params = {
        "t": title,
        "apikey": api_key,
    }

    try:
        resp = await client.get(EXTERNAL_API_BASE_URL, params=params, timeout=10.0)
        resp.raise_for_status()
    except httpx.HTTPError:
        return None

    data = resp.json()

    # Shape this into the fields our frontend expects
    return {
        "poster_url": data.get("poster_url") or data.get("Poster"),
        "runtime": data.get("runtime") or data.get("Runtime"),
        "cast": data.get("cast") or data.get("Actors"),
    }


async def _update_item_from_external(
    client: httpx.AsyncClient,
    item: JsonObj,
) -> bool:
    """Enrich a single movie item in-place.

    Returns True if any field changed; False otherwise.
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
        # Only overwrite if the API gave us a non-empty value and it differs
        if value and item.get(key) != value:
            item[key] = value
            changed = True

    return changed


# ---------------------------------------------------------------------------
# Public API used by router + tests
# ---------------------------------------------------------------------------


async def sync_external_metadata() -> Tuple[int, str]:
    """Sync external metadata into movies.json.

    Returns:
        (items_updated_count, timestamp_str)
    """
    items = _load_json(MOVIES_FILE)
    if not isinstance(items, list):
        # If the file is somehow malformed, don't crash the admin call
        timestamp = datetime.now(UTC).isoformat()
        return 0, timestamp

    updated_indices: List[int] = []
    timestamp = datetime.now(UTC).isoformat()

    async with httpx.AsyncClient() as client:
        for idx, item in enumerate(items):
            if await _update_item_from_external(client, item):
                updated_indices.append(idx)

    # Persist movies only if something changed
    if updated_indices:
        _save_json(MOVIES_FILE, items)

    # Append to sync log
    log = _load_json(SYNC_LOG_FILE) or []
    if not isinstance(log, list):
        log = []

    log.append(
        {
            "timestamp": timestamp,
            "items_updated": len(updated_indices),
            "indices": updated_indices,
        }
    )
    _save_json(SYNC_LOG_FILE, log)

    return len(updated_indices), timestamp
