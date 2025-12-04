from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import pytest
from pytest_mock import MockerFixture

from backend.services import external_sync_service as sync_mod


def _write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=4), encoding="utf-8")


@pytest.fixture
def anyio_backend() -> str:
    # pytest-anyio: we only use asyncio
    return "asyncio"


@pytest.mark.anyio
async def test_sync_external_metadata_updates_movies_and_logs(
    tmp_path: Path,
    mocker: MockerFixture,
) -> None:
    """Service should enrich exactly one movie and log the sync."""

    movies_file = tmp_path / "movies.json"
    log_file = tmp_path / "external_sync_log.json"

    # Point service paths to temp files
    mocker.patch.object(sync_mod, "MOVIES_FILE", movies_file)
    mocker.patch.object(sync_mod, "SYNC_LOG_FILE", log_file)

    # Seed with one bare movie + one already enriched movie
    items: List[Dict[str, Any]] = [
        {
            "id": "m1",
            "title": "Avengers Endgame",
        },
        {
            "id": "m2",
            "title": "Existing Movie",
            "poster_url": "http://existing/poster.jpg",
            "runtime": "120 min",
            "cast": "Actor One, Actor Two",
        },
    ]
    _write_json(movies_file, items)

    # Fake external API result for Avengers only
    async def fake_fetch(client, title: str):
        if title == "Avengers Endgame":
            return {
                "poster_url": "http://example.com/avengers.jpg",
                "runtime": "181 min",
                "cast": "Robert Downey Jr., Chris Evans",
            }
        return None

    mocker.patch.object(sync_mod, "_fetch_external_metadata", fake_fetch)

    updated_count, ts = await sync_mod.sync_external_metadata()

    assert updated_count == 1
    assert isinstance(ts, str)

    # Movies file should be updated
    updated_items = json.loads(movies_file.read_text(encoding="utf-8"))
    assert len(updated_items) == 2

    first = updated_items[0]
    assert first["poster_url"] == "http://example.com/avengers.jpg"
    assert "Robert Downey Jr." in first["cast"]

    # Second movie unchanged
    second = updated_items[1]
    assert second["poster_url"] == "http://existing/poster.jpg"

    # Log file should contain one entry
    log = json.loads(log_file.read_text(encoding="utf-8"))
    assert isinstance(log, list)
    assert len(log) == 1
    entry = log[0]
    assert entry["items_updated"] == 1
    assert entry["indices"] == [0]
    assert isinstance(entry["timestamp"], str)
