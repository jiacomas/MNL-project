from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import pytest
from pytest_mock import MockerFixture

from backend.services import history_service as svc


def _write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=4), encoding="utf-8")


def test_log_view_creates_and_updates_single_entry(
    tmp_path: Path,
    mocker: MockerFixture,
) -> None:
    """When a movie page is opened, it is logged (and updated on repeat views)."""
    history_file = tmp_path / "history.json"
    items_file = tmp_path / "items.json"

    # Patch the service to use temp files
    mocker.patch.object(svc, "HISTORY_FILE", history_file)
    mocker.patch.object(svc, "ITEMS_FILE", items_file)

    # Seed an items file (not used directly in this test but required by service)
    _write_json(
        items_file,
        [{"id": "m1", "title": "Movie 1", "year": 2020}],
    )

    # First view
    svc.log_view("u1", "m1", viewed_at="2025-01-01T10:00:00+00:00")
    # Second view later – should update the same record
    svc.log_view("u1", "m1", viewed_at="2025-01-02T12:00:00+00:00")

    assert history_file.exists()
    rows: List[Dict[str, Any]] = json.loads(history_file.read_text(encoding="utf-8"))
    assert len(rows) == 1

    entry = rows[0]
    assert entry["user_id"] == "u1"
    assert entry["movie_id"] == "m1"
    assert entry["last_viewed_at"] == "2025-01-02T12:00:00+00:00"


def test_list_history_joins_movie_metadata_and_sorts(
    tmp_path: Path,
    mocker: MockerFixture,
) -> None:
    """Users can view history with title + release year + last viewed date."""
    history_file = tmp_path / "history.json"
    items_file = tmp_path / "items.json"

    mocker.patch.object(svc, "HISTORY_FILE", history_file)
    mocker.patch.object(svc, "ITEMS_FILE", items_file)

    # Seed movies
    _write_json(
        items_file,
        [
            {"id": "m1", "title": "Action One", "year": 2019},
            {"id": "m2", "title": "Drama Two", "year": 2020},
            {"id": "m3", "title": "Comedy Three", "year": 2021},
        ],
    )

    # Seed history for multiple users
    _write_json(
        history_file,
        [
            {
                "user_id": "u1",
                "movie_id": "m1",
                "last_viewed_at": "2025-01-02T12:00:00+00:00",
            },
            {
                "user_id": "u1",
                "movie_id": "m2",
                "last_viewed_at": "2025-01-03T09:00:00+00:00",
            },
            {
                "user_id": "u2",
                "movie_id": "m3",
                "last_viewed_at": "2025-01-04T09:00:00+00:00",
            },
        ],
    )

    history = svc.list_history("u1")

    # Only user u1's items
    assert [h["movie_id"] for h in history] == ["m2", "m1"]

    # Joined metadata
    first = history[0]
    assert first["title"] == "Drama Two"
    assert first["release_year"] == 2020
    assert first["last_viewed_at"] == "2025-01-03T09:00:00+00:00"


def test_clear_history_item_and_all(
    tmp_path: Path,
    mocker: MockerFixture,
) -> None:
    """User can clear individual items or their entire history."""
    history_file = tmp_path / "history.json"
    items_file = tmp_path / "items.json"

    mocker.patch.object(svc, "HISTORY_FILE", history_file)
    mocker.patch.object(svc, "ITEMS_FILE", items_file)

    _write_json(
        items_file,
        [{"id": "m1", "title": "Movie 1", "year": 2020}],
    )

    _write_json(
        history_file,
        [
            {"user_id": "u1", "movie_id": "m1", "last_viewed_at": "2025-01-01T00:00:00"},
            {"user_id": "u1", "movie_id": "m2", "last_viewed_at": "2025-01-02T00:00:00"},
            {"user_id": "u2", "movie_id": "m3", "last_viewed_at": "2025-01-03T00:00:00"},
        ],
    )

    # Clear single movie for u1
    svc.clear_history_item("u1", "m1")
    rows = json.loads(history_file.read_text(encoding="utf-8"))
    assert {"user_id": "u1", "movie_id": "m1"} not in [
        {"user_id": r["user_id"], "movie_id": r["movie_id"]} for r in rows
    ]

    # Clear all history for u1
    svc.clear_history("u1")
    rows = json.loads(history_file.read_text(encoding="utf-8"))

    # Only u2's record should remain
    assert len(rows) == 1
    assert rows[0]["user_id"] == "u2"
