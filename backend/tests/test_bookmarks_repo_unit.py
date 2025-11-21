"""
Tests for the Bookmarks repository.
This test uses tmp_path to avoid touching real files.
"""

import csv
import uuid
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

import pytest

from backend.repositories.bookmarks_repo import JSONBookmarkRepo
from backend.schemas.bookmarks import BookmarkCreate


def sample_bookmark(movie_id: str = "movie_67890") -> BookmarkCreate:
    """Helper to create a sample BookmarkCreate instance for testing."""
    return BookmarkCreate(movie_id=movie_id)


# -------------------- CREATE -------------------- #
def test_create_persists_bookmark(tmp_path, mocker):
    repo = JSONBookmarkRepo(storage_path=str(tmp_path / "bookmarks.json"))

    # Mock no existing bookmarks
    mocker.patch.object(repo, "_load", return_value=[])

    # Capture saved data
    saved = []
    mocker.patch.object(repo, "_save", side_effect=lambda data: saved.extend(data))

    created = repo.create(sample_bookmark("movie_1"), user_id="user_1")

    assert created.user_id == "user_1"
    assert created.movie_id == "movie_1"
    assert isinstance(created.id, UUID)
    assert created.created_at.tzinfo is not None  # tz-aware

    assert len(saved) == 1
    row = saved[0]
    assert row["user_id"] == "user_1"
    assert row["movie_id"] == "movie_1"
    assert isinstance(row["created_at"], datetime)


def test_create_duplicate_prevented(tmp_path, mocker):
    repo = JSONBookmarkRepo(storage_path=str(tmp_path / "bookmarks.json"))
    mocker.patch.object(
        repo, "_load", return_value=[{"user_id": "user_1", "movie_id": "movie_1"}]
    )

    with pytest.raises(ValueError):
        repo.create(sample_bookmark("movie_1"), user_id="user_1")


# -------------------- LIST -------------------- #
def test_list_all_bookmarks(tmp_path, mocker):
    repo = JSONBookmarkRepo(storage_path=str(tmp_path / "bookmarks.json"))

    now = datetime.now(timezone.utc).isoformat()
    fake_data = [
        {
            "id": str(uuid.uuid4()),
            "user_id": "u1",
            "movie_id": "m1",
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": str(uuid.uuid4()),
            "user_id": "u2",
            "movie_id": "m2",
            "created_at": now,
            "updated_at": now,
        },
    ]
    mocker.patch.object(repo, "_load", return_value=fake_data)

    bookmarks = repo.list_all()
    assert len(bookmarks) == 2
    assert all(isinstance(bk.created_at, datetime) for bk in bookmarks)


# -------------------- GET -------------------- #
def test_get_bookmarks_by_user(tmp_path, mocker):
    repo = JSONBookmarkRepo(storage_path=str(tmp_path / "bookmarks.json"))

    now = datetime.now(timezone.utc).isoformat()
    fake_data = [
        {
            "id": str(uuid.uuid4()),
            "user_id": "u1",
            "movie_id": "m1",
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": str(uuid.uuid4()),
            "user_id": "u1",
            "movie_id": "m2",
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": str(uuid.uuid4()),
            "user_id": "u2",
            "movie_id": "m3",
            "created_at": now,
            "updated_at": now,
        },
    ]
    mocker.patch.object(repo, "_load", return_value=fake_data)

    results = repo.get_bookmarks_by_user("u1")
    assert len(results) == 2
    assert {bk.movie_id for bk in results} == {"m1", "m2"}


def test_get_bookmarks_by_movie(tmp_path, mocker):
    repo = JSONBookmarkRepo(storage_path=str(tmp_path / "bookmarks.json"))
    now = datetime.now(timezone.utc).isoformat()

    fake_data = [
        {
            "id": str(uuid.uuid4()),
            "user_id": "u1",
            "movie_id": "m1",
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": str(uuid.uuid4()),
            "user_id": "u2",
            "movie_id": "m1",
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": str(uuid.uuid4()),
            "user_id": "u3",
            "movie_id": "m2",
            "created_at": now,
            "updated_at": now,
        },
    ]
    mocker.patch.object(repo, "_load", return_value=fake_data)

    results = repo.get_bookmarks_by_movie("m1")
    assert len(results) == 2
    assert {bk.user_id for bk in results} == {"u1", "u2"}


def test_get_missing_fields_are_filled(tmp_path, mocker):
    """Ensure missing created_at/updated_at is auto-filled."""
    repo = JSONBookmarkRepo(storage_path=str(tmp_path / "bookmarks.json"))
    fake_data = [{"id": str(uuid.uuid4()), "user_id": "u1", "movie_id": "m1"}]

    mocker.patch.object(repo, "_load", return_value=fake_data)
    results = repo.list_all()

    assert len(results) == 1
    assert isinstance(results[0].created_at, datetime)
    assert results[0].created_at.tzinfo is not None


# -------------------- DELETE -------------------- #
def test_delete_bookmark(tmp_path, mocker):
    repo = JSONBookmarkRepo(storage_path=str(tmp_path / "bookmarks.json"))

    b1 = {"id": "id_1"}
    b2 = {"id": "id_2"}

    mocker.patch.object(repo, "_load", side_effect=[[b1, b2], [b2], [b2]])
    saved = []
    mocker.patch.object(repo, "_save", side_effect=lambda data: saved.extend(data))

    assert repo.delete("id_1") is True
    assert saved == [b2]
    assert repo.delete("id_1") is False


def test_delete_accepts_uuid_instance(tmp_path, mocker):
    repo = JSONBookmarkRepo(storage_path=str(tmp_path / "bookmarks.json"))
    uid = uuid.uuid4()

    mocker.patch.object(repo, "_load", return_value=[{"id": str(uid)}])
    saved = []
    mocker.patch.object(repo, "_save", side_effect=lambda data: saved.extend(data))

    assert repo.delete(uid) is True


# -------------------- EXPORT -------------------- #
def test_export_to_csv(tmp_path):
    repo = JSONBookmarkRepo(storage_path=str(tmp_path / "bookmarks.json"))

    repo.create(sample_bookmark("m1"), user_id="u1")
    repo.create(sample_bookmark("m2"), user_id="u2")

    export_dir = tmp_path / "exports"
    export_path = repo.export_to_csv(str(export_dir))
    assert Path(export_path).exists()

    rows = list(csv.DictReader(open(export_path)))
    assert len(rows) == 2
    assert set(rows[0].keys()) == {
        "id",
        "user_id",
        "movie_id",
        "created_at",
        "updated_at",
    }

    # ISO timestamp check
    assert "T" in rows[0]["created_at"]
