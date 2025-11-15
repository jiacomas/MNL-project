# backend/tests/test_bookmarks_service.py
import uuid
from pathlib import Path

from backend.repositories.bookmarks_repo import JSONBookmarkRepo
from backend.schemas.bookmarks import BookmarkCreate
from backend.services.bookmarks_service import BookmarkService


def setup_service(tmp_path):
    '''Build an isolated repo+service using a temp directory.'''
    storage_path = tmp_path / "bookmarks.json"
    export_dir = tmp_path / "exports"

    repo = JSONBookmarkRepo(str(storage_path))
    # Monkeypatch export_dir manually
    repo.export_dir = str(export_dir)

    svc = BookmarkService(repo)
    return svc, repo, export_dir


def test_create_bookmark(tmp_path):
    svc, repo, _ = setup_service(tmp_path)

    payload = BookmarkCreate(user_id="u1", movie_id="m1")
    out = svc.create_bookmark(payload)

    assert out.user_id == "u1"
    assert out.movie_id == "m1"

    assert isinstance(out.id, uuid.UUID)  # validates UUID


def test_no_duplicate_bookmark(tmp_path):
    svc, repo, _ = setup_service(tmp_path)

    svc.create_bookmark(BookmarkCreate(user_id="u1", movie_id="m1"))

    # second create should fail
    import pytest
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as e:
        svc.create_bookmark(BookmarkCreate(user_id="u1", movie_id="m1"))

    assert e.value.status_code == 409


def test_list_bookmarks(tmp_path):
    svc, repo, _ = setup_service(tmp_path)

    svc.create_bookmark(BookmarkCreate(user_id="u1", movie_id="m1"))
    svc.create_bookmark(BookmarkCreate(user_id="u2", movie_id="m2"))

    all_items = svc.list_bookmarks()
    assert len(all_items) == 2

    user1_items = svc.list_bookmarks("u1")
    assert len(user1_items) == 1
    assert user1_items[0].user_id == "u1"


def test_delete_bookmark(tmp_path):
    svc, repo, _ = setup_service(tmp_path)

    created = svc.create_bookmark(BookmarkCreate(user_id="u1", movie_id="m1"))

    # first delete should succeed
    svc.delete_bookmark(created.id)

    # second delete should raise 404
    import pytest
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as e:
        svc.delete_bookmark(created.id)

    assert e.value.status_code == 404


def test_export_bookmarks(tmp_path):
    svc, repo, export_dir = setup_service(tmp_path)

    svc.create_bookmark(BookmarkCreate(user_id="u1", movie_id="m1"))

    export_path = svc.export_bookmarks()
    csv_file = Path(export_path)

    assert csv_file.exists()

    content = csv_file.read_text(encoding="utf-8")
    assert "user_id" in content
    assert "movie_id" in content
