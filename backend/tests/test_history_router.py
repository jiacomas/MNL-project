from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pytest_mock import MockerFixture

from backend.routers import history as history_router
from backend.services import history_service


def _create_app() -> FastAPI:
    app = FastAPI()
    app.include_router(history_router.router)
    return app


def _make_client(tmp_path: Path, mocker: MockerFixture) -> TestClient:
    """Patch HISTORY_ROOT to tmp_path and return a TestClient."""
    mocker.patch.object(history_service, "HISTORY_ROOT", tmp_path)
    app = _create_app()
    return TestClient(app)


def test_log_and_list_history(tmp_path: Path, mocker: MockerFixture) -> None:
    """Logging a view should create an entry that appears in GET /history/{user_id}."""
    client = _make_client(tmp_path, mocker)

    # Log a view
    resp = client.post("/history/u1/m1")
    assert resp.status_code == 204

    # List history
    resp = client.get("/history/u1")
    assert resp.status_code == 200

    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 1

    entry = data[0]
    assert entry["movie_id"] == "m1"
    assert "last_viewed_at" in entry  # timestamp logged
    # Optional fields can be absent or null
    assert "title" in entry
    assert "release_year" in entry


def test_clear_single_item(tmp_path: Path, mocker: MockerFixture) -> None:
    """DELETE /history/{user_id}/{movie_id} should remove only that movie."""
    client = _make_client(tmp_path, mocker)

    # Seed two views
    client.post("/history/u1/m1")
    client.post("/history/u1/m2")

    # Sanity check
    resp = client.get("/history/u1")
    assert len(resp.json()) == 2

    # Clear one movie
    resp = client.delete("/history/u1/m1")
    assert resp.status_code == 204

    # Only m2 should remain
    resp = client.get("/history/u1")
    movies_remaining = {e["movie_id"] for e in resp.json()}
    assert movies_remaining == {"m2"}


def test_clear_all_history(tmp_path: Path, mocker: MockerFixture) -> None:
    """DELETE /history/{user_id} should remove all entries."""
    client = _make_client(tmp_path, mocker)

    client.post("/history/u1/m1")
    client.post("/history/u1/m2")

    # Clear everything
    resp = client.delete("/history/u1")
    assert resp.status_code == 204

    resp = client.get("/history/u1")
    assert resp.status_code == 200
    assert resp.json() == []
