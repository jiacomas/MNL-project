from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import pytest

from backend.services import external_sync_service as sync_mod

pytestmark = pytest.mark.anyio  # apply "anyio" to the whole module


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=4), encoding="utf-8")


async def fake_fetch(client, title: str) -> Dict[str, Any] | None:
    """Fake external metadata fetch for testing only."""
    if title == "Avengers Endgame":
        return {
            "poster_url": "http://example.com/avengers.jpg",
            "runtime": 181,
            "cast": "Robert Downey Jr., Chris Evans",
        }
    return None


async def test_sync_external_metadata_updates_items_and_logs(tmp_path, monkeypatch):
    """Validate that external sync:

    - Enriches only movies missing metadata
    - Leaves already-complete movies unchanged
    - Logs sync metadata: timestamp, updated count, indices
    """

    # --------------------------------------------------------------
    # Setup temp storage
    # --------------------------------------------------------------
    items_file = tmp_path / "items.json"
    log_file = tmp_path / "external_sync_log.json"

    monkeypatch.setattr(sync_mod, "ITEMS_FILE", items_file)
    monkeypatch.setattr(sync_mod, "SYNC_LOG_FILE", log_file)
    monkeypatch.setattr(sync_mod, "_fetch_external_metadata", fake_fetch)

    # Seed two movies: one missing metadata, one already enriched
    items_seed = [
        {"id": "m1", "title": "Avengers Endgame"},
        {
            "id": "m2",
            "title": "Some Other Movie",
            "poster_url": "http://existing/poster.jpg",
            "runtime": 120,
            "cast": "Actor One, Actor Two",
        },
    ]
    write_json(items_file, items_seed)

    # --------------------------------------------------------------
    # Execute sync
    # --------------------------------------------------------------
    updated_count, timestamp = await sync_mod.sync_external_metadata()

    assert updated_count == 1
    assert isinstance(timestamp, str)

    # --------------------------------------------------------------
    # Validate updated items.json
    # --------------------------------------------------------------
    updated_items = json.loads(items_file.read_text())

    # Should still be exactly 2 items
    assert len(updated_items) == 2

    first = updated_items[0]
    second = updated_items[1]

    # First item enriched by fake API
    assert first["title"] == "Avengers Endgame"
    assert first["poster_url"] == "http://example.com/avengers.jpg"
    assert first["runtime"] == 181
    assert "Robert Downey Jr." in first["cast"]

    # Second item unchanged
    assert second["poster_url"] == "http://existing/poster.jpg"
    assert second["runtime"] == 120
    assert second["cast"] == "Actor One, Actor Two"

    # --------------------------------------------------------------
    # Validate log file
    # --------------------------------------------------------------
    log = json.loads(log_file.read_text())
    assert isinstance(log, list)
    assert len(log) == 1

    entry = log[0]
    assert entry["items_updated"] == 1
    assert entry["indices"] == [0]
    assert isinstance(entry["timestamp"], str)
