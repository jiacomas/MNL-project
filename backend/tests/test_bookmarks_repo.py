# backend/tests/test_bookmarks_repo.py

'''
Tests for the Bookmarks repository.
This test uses tmp_path to avoid touching real files.
'''

import csv
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from repositories.bookmarks_repo import JSONBookmarkRepo
from schemas.bookmarks import BookmarkCreate, BookmarkOut


# Helpers
def make_repo(tmp_path: Path) -> tuple[JSONBookmarkRepo, str]:
    '''
    Create a repo instance that writes to a temp CSV file.
    Returns the repo and the file path.
    '''
    data_path = tmp_path / "bookmarks.json"
    export_dir = tmp_path / "exports"
    repo = JSONBookmarkRepo(storage_path=str(data_path))
    return repo, str(export_dir)


def sample_bookmark(
    user_id: str = "user_12345",
    movie_id: str = "movie_67890",
) -> BookmarkCreate:
    '''
    Help to create a sample BookmarkCreate instance for testing.
    '''
    return BookmarkCreate(user_id=user_id, movie_id=movie_id)


# Tests
def test_create_persists_bookmark(tmp_path: Path):
    '''Ensure create() stores a bookmark in the JSON file'''
    repo, _ = make_repo(tmp_path)
    bookmark = sample_bookmark("user_1", "movie_1")

    created = repo.create(bookmark)
    # object level assertions
    assert isinstance(created, BookmarkOut)
    assert created.user_id == "user_1"
    assert created.movie_id == "movie_1"
    # id must ve UUIDv4
    assert isinstance(created.id, UUID)
    assert created.id.version == 4
    # tz-aware timestamps
    assert created.created_at.tzinfo is not None
    assert created.updated_at.tzinfo is not None

    # Verify file contents
    storage = Path(repo.storage_path)
    with storage.open("r", encoding="utf-8") as f:
        data = json.load(f)

    assert isinstance(data, list) and len(data) == 1
    row = data[0]
    assert row["user_id"] == "user_1"
    assert row["movie_id"] == "movie_1"

    # persisted timestamps are ISO strings
    assert isinstance(row["created_at"], str)
    assert isinstance(row["updated_at"], str)

    # persisted timestamps are ISO strings
    assert isinstance(row["created_at"], str)
    assert isinstance(row["updated_at"], str)


def test_list_all_bookmarks(tmp_path: Path):
    '''Ensure list_all() correctly reads all bookmarks'''
    repo, _ = make_repo(tmp_path)
    now = datetime.now(timezone.utc)

    # Seed data
    payload = [
        {
            "id": str(uuid.uuid4()),
            "user_id": "user_1",
            "movie_id": "movie_1",
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        },
        {
            "id": str(uuid.uuid4()),
            "user_id": "user_2",
            "movie_id": "movie_2",
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        },
    ]
    Path(repo.storage_path).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # Call list_all
    bookmarks = repo.list_all()
    # Verify ids
    for bk in bookmarks:
        uuid.UUID(str(bk.id), version=4)
    # Verify timestamps are parsed correctly
    assert all(isinstance(bk.created_at, datetime) for bk in bookmarks)
    assert all(bk.created_at.tzinfo is not None for bk in bookmarks)


def test_get_by_user(tmp_path: Path):
    '''Ensure get_by_user() filters bookmarks correctly'''
    repo, _ = make_repo(tmp_path)
    repo.create(sample_bookmark("user_1", "movie_1"))
    repo.create(sample_bookmark("user_1", "movie_2"))
    repo.create(sample_bookmark("user_2", "movie_3"))

    results = repo.get_by_user("user_1")
    assert all(bk.user_id == "user_1" for bk in results)
    assert len(results) == 2


def test_delete_bookmark(tmp_path: Path):
    '''Ensure delete() removes a bookmark'''
    repo, _ = make_repo(tmp_path)
    b1 = repo.create(sample_bookmark("user_1", "movie_1"))
    b2 = repo.create(sample_bookmark("user_2", "movie_2"))

    # Delete one bookmark
    deleted = repo.delete(str(b1.id))
    assert deleted is True

    # Try deleting again (should not exist)
    deleted_again = repo.delete(str(b1.id))
    assert deleted_again is False

    # Verify file has only one remaining
    with open(repo.storage_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert len(data) == 1
    assert data[0]["id"] == str(b2.id)


def test_export_to_csv(tmp_path: Path):
    '''Ensure export_to_csv() writes a valid CSV file'''
    repo, export_dir = make_repo(tmp_path)
    repo.create(sample_bookmark("user_1", "movie_1"))
    repo.create(sample_bookmark("user_2", "movie_2"))

    export_path = repo.export_to_csv(export_dir)
    assert Path(export_path).exists()

    with open(export_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    assert len(rows) == 2
    assert set(rows[0].keys()) == {
        "id",
        "user_id",
        "movie_id",
        "created_at",
        "updated_at",
    }
