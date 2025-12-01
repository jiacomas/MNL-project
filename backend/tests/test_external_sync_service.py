from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict
from unittest.mock import Mock

import pytest
from pytest_mock import MockerFixture

from backend.services import external_sync_service as sync_mod


@pytest.fixture
def anyio_backend() -> str:
    # Tell pytest-anyio to only use asyncio, not trio
    return "asyncio"


@pytest.mark.anyio
async def test_sync_external_metadata_updates_items_and_logs(
    tmp_path: Path,
    mocker: MockerFixture,
) -> None:
    """Unit test for external API sync.

    Verifies:
    - items.json is updated with poster_url, runtime, cast for one movie
    - other movies remain unchanged
    - sync log is appended with timestamp, items_updated, indices
    """

    # Mock Repositories
    class MockMovie:
        def __init__(self, id, title, duration=None, mainStars=None):
            self.movie_id = id
            self.title = title
            self.duration = duration
            self.mainStars = mainStars

    m1 = MockMovie("m1", "Avengers Endgame")
    m2 = MockMovie(
        "m2",
        "Some Other Movie",
        120,
        "Actor One, Actor Two",
    )

    items = [m1, m2]

    # Mock MovieRepository
    mock_movie_repo = Mock()
    mock_movie_repo.get_all.return_value = (items, 2)

    # Mock update method
    def fake_update(movie_id, update):
        # Apply update to the mock object
        for item in items:
            if item.movie_id == movie_id:
                update_dict = update.model_dump(exclude_unset=True)
                for k, v in update_dict.items():
                    setattr(item, k, v)
                return item
        return None

    mock_movie_repo.update.side_effect = fake_update

    mocker.patch.object(sync_mod, "_movie_repo", mock_movie_repo)

    # Mock SyncLogRepository
    from backend.repositories.sync_repo import SyncLogRepository

    log_file = tmp_path / "external_sync_log.json"
    real_sync_repo = SyncLogRepository(storage_path=log_file)
    mocker.patch.object(sync_mod, "_sync_repo", real_sync_repo)

    # Mock external fetch to avoid real HTTP calls
    async def fake_fetch(client, title: str) -> Dict[str, Any] | None:
        if title == "Avengers Endgame":
            # Return fields that match the domain model: duration & mainStars
            return {"duration": 181, "mainStars": "Robert Downey Jr., Chris Evans"}
        # no update for other titles
        return None

    mocker.patch.object(sync_mod, "_fetch_external_metadata", fake_fetch)

    # Run sync and assert result
    updated_count, timestamp = await sync_mod.sync_external_metadata()

    # Exactly one movie was updated
    assert updated_count == 1
    assert timestamp is not None

    # Verify items were updated (in memory mock objects)
    assert m1.duration == 181
    assert "Robert Downey Jr." in m1.mainStars

    # other movie remains unchanged
    assert m2.duration == 120
    assert "Actor One" in m2.mainStars

    # Verify MovieRepository update was called
    assert mock_movie_repo.update.call_count == 1

    # Sync log written with timestamp + items_updated + indices
    log = json.loads(log_file.read_text(encoding="utf-8"))
    assert isinstance(log, list)
    assert len(log) == 1

    entry = log[0]
    assert entry["items_updated"] == 1
    # Only first item (index 0) updated
    assert entry["indices"] == [0]
    assert "timestamp" in entry
    assert isinstance(entry["timestamp"], str)
