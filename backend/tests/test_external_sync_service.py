from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pytest

from services import external_sync_service as sync_mod

@pytest.fixture
def anyio_backend():
    # Tell pytest-anyio to only use asyncio, not trio
    return "asyncio"

def _write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=4), encoding="utf-8")


@pytest.mark.anyio
async def test_sync_external_metadata_updates_items_and_logs(tmp_path, monkeypatch) -> None:
    """Unit test for external API sync.

    Verifies:
    - items.json is updated with poster_url, runtime, cast for one movie
    - other movies remain unchanged
    - sync log is appended with timestamp, items_updated, indices
    """

    # ------------------------------------------------------------------
    # 1. Point service to temp files
    # ------------------------------------------------------------------
    items_file = tmp_path / "items.json"
    log_file = tmp_path / "external_sync_log.json"

    monkeypatch.setattr(sync_mod, "ITEMS_FILE", items_file)
    monkeypatch.setattr(sync_mod, "SYNC_LOG_FILE", log_file)

    # ------------------------------------------------------------------
    # 2. Seed items: one missing metadata, one already enriched
    # ------------------------------------------------------------------
    items: List[Dict[str, Any]] = [
        {
            "id": "m1",
            "title": "Avengers Endgame",
            # no poster/runtime/cast yet
        },
        {
            "id": "m2",
            "title": "Some Other Movie",
            "poster_url": "http://existing/poster.jpg",
            "runtime": 120,
            "cast": "Actor One, Actor Two",
        },
    ]
    _write_json(items_file, items)

    # ------------------------------------------------------------------
    # 3. Monkeypatch external fetch to avoid real HTTP calls
    # ------------------------------------------------------------------
    async def fake_fetch(client, title: str) -> Dict[str, Any] | None:
        if title == "Avengers Endgame":
            return {
                "poster_url": "http://example.com/avengers.jpg",
                "runtime": 181,
                "cast": "Robert Downey Jr., Chris Evans",
            }
        # no update for other titles
        return None

    monkeypatch.setattr(sync_mod, "_fetch_external_metadata", fake_fetch)

    # ------------------------------------------------------------------
    # 4. Run sync and assert result
    # ------------------------------------------------------------------
    updated_count, timestamp = await sync_mod.sync_external_metadata()

    # Exactly one movie was updated
    assert updated_count == 1
    assert timestamp is not None

    updated_items = json.loads(items_file.read_text(encoding="utf-8"))
    assert len(updated_items) == 2

    # First item enriched from external metadata
    first = updated_items[0]
    assert first["title"] == "Avengers Endgame"
    assert first["poster_url"] == "http://example.com/avengers.jpg"
    assert first["runtime"] == 181
    assert "Robert Downey Jr." in first["cast"]

    # Second item unchanged
    second = updated_items[1]
    assert second["poster_url"] == "http://existing/poster.jpg"
    assert second["runtime"] == 120
    assert second["cast"] == "Actor One, Actor Two"

    # ------------------------------------------------------------------
    # 5. Sync log written with timestamp + items_updated + indices
    # ------------------------------------------------------------------
    log = json.loads(log_file.read_text(encoding="utf-8"))
    assert isinstance(log, list)
    assert len(log) == 1

    entry = log[0]
    assert entry["items_updated"] == 1
    # Only first item (index 0) updated
    assert entry["indices"] == [0]
    assert "timestamp" in entry
    assert isinstance(entry["timestamp"], str)
