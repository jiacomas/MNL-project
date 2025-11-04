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

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

import httpx  # add to requirements.txt

SERVICES_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SERVICES_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent

ROOT_DATA_DIR = PROJECT_ROOT / "data"
ITEMS_FILE = ROOT_DATA_DIR / "items.json"
SYNC_LOG_FILE = ROOT_DATA_DIR / "external_sync_log.json"

# Replace with the real API you choose (e.g. OMDb/TMDB)
EXTERNAL_API_BASE_URL = "https://example.com/movie-api"
EXTERNAL_API_KEY_ENV = "MOVIE_API_KEY"  # env var with your key


def _load_json(path: Path) -> Any:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _save_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=4), encoding="utf-8")


async def _fetch_external_metadata(
    client: httpx.AsyncClient, title: str
) -> Dict | None:
    """
    Fetches metadata from external API by title.

    You must adapt query params & field mapping to the real API.
    """
    api_key = os.getenv(EXTERNAL_API_KEY_ENV)
    if not api_key:
        # In dev, if no key is set, we just skip.
        return None

    params = {"title": title, "api_key": api_key}

    try:
        resp = await client.get(EXTERNAL_API_BASE_URL, params=params, timeout=10.0)
        resp.raise_for_status()
    except httpx.HTTPError:
        return None

    data = resp.json()

    # Map remote fields into our schema; adjust to match your API response.
    return {
        "poster_url": data.get("poster_url") or data.get("Poster"),
        "runtime": data.get("runtime") or data.get("Runtime"),
        "cast": data.get("cast") or data.get("Actors"),
    }


async def sync_external_metadata() -> Tuple[int, datetime]:
    """
    Syncs external metadata into items.json.

    Returns:
        (items_updated_count, timestamp)
    """
    items = _load_json(ITEMS_FILE)
    if not isinstance(items, list):
        return 0, datetime.now(UTC)

    updated_indices: List[int] = []
    now = datetime.now(UTC)

    async with httpx.AsyncClient() as client:
        for index, item in enumerate(items):
            title = item.get("title")
            if not title:
                continue

            external = await _fetch_external_metadata(client, title)
            if not external:
                continue

            changed = False

            poster_url = external.get("poster_url")
            if poster_url and item.get("poster_url") != poster_url:
                item["poster_url"] = poster_url
                changed = True

            runtime = external.get("runtime")
            if runtime and item.get("runtime") != runtime:
                item["runtime"] = runtime
                changed = True

            cast = external.get("cast")
            if cast and item.get("cast") != cast:
                item["cast"] = cast
                changed = True

            if changed:
                updated_indices.append(index)

    if updated_indices:
        _save_json(ITEMS_FILE, items)

    # Log the sync
    log = _load_json(SYNC_LOG_FILE) or []
    if not isinstance(log, list):
        log = []

    log.append(
        {
            "timestamp": now.isoformat(),
            "items_updated": len(updated_indices),
            "indices": updated_indices,
        }
    )
    _save_json(SYNC_LOG_FILE, log)

    return len(updated_indices), now
