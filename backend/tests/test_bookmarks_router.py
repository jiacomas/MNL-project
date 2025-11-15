import uuid
from pathlib import Path

from fastapi.testclient import TestClient

from backend.main import app
from backend.repositories.bookmarks_repo import JSONBookmarkRepo

client = TestClient(app)


def setup_tmp_repo(tmp_path, monkeypatch):
    '''Inject temp JSON repo path into BOOKMARKS_PATH env var.'''
    fake_path = tmp_path / "bookmarks.json"
    export_dir = tmp_path / "exports"

    monkeypatch.setenv("BOOKMARKS_PATH", str(fake_path))
    monkeypatch.setenv("BOOKMARKS_EXPORT_DIR", str(export_dir))

    return JSONBookmarkRepo(str(fake_path))


def test_create_bookmark(tmp_path, monkeypatch):
    '''POST /bookmarks/ should create a new bookmark'''
    setup_tmp_repo(tmp_path, monkeypatch)

    payload = {"user_id": "u1", "movie_id": "m1"}

    res = client.post("/bookmarks/", json=payload)
    assert res.status_code == 200

    body = res.json()
    assert body["user_id"] == "u1"
    assert body["movie_id"] == "m1"
    assert "id" in body
    uuid.UUID(body["id"])  # validate UUIDv4


def test_list_bookmarks(tmp_path, monkeypatch):
    '''GET /bookmarks/ should return all bookmarks.'''
    setup_tmp_repo(tmp_path, monkeypatch)

    # seed 2 bookmarks
    client.post("/bookmarks/", json={"user_id": "u1", "movie_id": "m1"})
    client.post("/bookmarks/", json={"user_id": "u2", "movie_id": "m2"})

    res = client.get("/bookmarks/")
    assert res.status_code == 200

    arr = res.json()
    assert isinstance(arr, list)
    assert len(arr) == 2


def test_delete_bookmark(tmp_path, monkeypatch):
    '''DELETE /bookmarks/{id} should remove bookmark'''
    setup_tmp_repo(tmp_path, monkeypatch)

    created = client.post(
        "/bookmarks/", json={"user_id": "u1", "movie_id": "m1"}
    ).json()
    bid = created["id"]

    res = client.delete(f"/bookmarks/{bid}")
    assert res.status_code == 200
    assert res.json()["deleted"] is True

    # second delete -> not found
    res2 = client.delete(f"/bookmarks/{bid}")
    assert res2.status_code == 404


def test_export_bookmarks(tmp_path, monkeypatch):
    '''GET /bookmarks/export should create a CSV file.'''
    setup_tmp_repo(tmp_path, monkeypatch)

    client.post("/bookmarks/", json={"user_id": "u1", "movie_id": "m1"})

    res = client.get("/bookmarks/export")
    assert res.status_code == 200

    csv_path = res.json()["export_path"]
    assert Path(csv_path).exists()

    csv_text = Path(csv_path).read_text(encoding="utf-8")
    assert "user_id" in csv_text
    assert "movie_id" in csv_text
