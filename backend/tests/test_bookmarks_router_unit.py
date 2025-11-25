from uuid import uuid4

from .conftest import now_iso


def test_list_bookmarks(client, mock_bookmarks_service, jwt_user_headers):
    bookmark_id = str(uuid4())

    mock_bookmarks_service.list_bookmarks.return_value = [
        {
            "id": bookmark_id,
            "user_id": "u1",
            "movie_id": "m1",
            "created_at": now_iso(),
            "updated_at": now_iso(),
        }
    ]

    r = client.get("/api/bookmarks", headers=jwt_user_headers)
    assert r.status_code == 200

    mock_bookmarks_service.list_bookmarks.assert_called_once_with("u1")


def test_create_bookmark(client, mock_bookmarks_service, jwt_user_headers):
    payload = {"movie_id": "m1"}
    bookmark_id = str(uuid4())

    mock_bookmarks_service.create_bookmark.return_value = {
        "id": bookmark_id,
        "user_id": "u1",
        "movie_id": "m1",
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }

    r = client.post("/api/bookmarks", json=payload, headers=jwt_user_headers)
    assert r.status_code in (200, 201)

    mock_bookmarks_service.create_bookmark.assert_called_once()
    args, kwargs = mock_bookmarks_service.create_bookmark.call_args

    bookmark_payload = args[0]
    user_id = args[1]

    assert getattr(bookmark_payload, "movie_id", None) == "m1"
    assert user_id == "u1"


def test_delete_bookmark(client, mock_bookmarks_service, jwt_user_headers):
    bookmark_id = str(uuid4())

    r = client.delete(f"/api/bookmarks/me/{bookmark_id}", headers=jwt_user_headers)
    assert r.status_code in (200, 204)

    mock_bookmarks_service.delete_bookmark.assert_called_once_with(
        bookmark_id, "u1", False
    )


def test_delete_bookmark_admin(client, mock_bookmarks_service, jwt_admin_headers):
    bookmark_id = str(uuid4())

    r = client.delete(f"/api/bookmarks/{bookmark_id}", headers=jwt_admin_headers)
    assert r.status_code in (200, 204)

    mock_bookmarks_service.delete_bookmark.assert_called_once_with(
        bookmark_id, "admin", True
    )


def test_export_bookmarks(client, mock_bookmarks_service, jwt_admin_headers):
    mock_bookmarks_service.export_bookmarks.return_value = "/tmp/bookmarks_export.csv"

    r = client.get("/api/bookmarks/export", headers=jwt_admin_headers)
    assert r.status_code == 200

    mock_bookmarks_service.export_bookmarks.assert_called_once()


def test_export_forbidden_for_user(client, jwt_user_headers):
    r = client.get("/api/bookmarks/export", headers=jwt_user_headers)
    assert r.status_code == 403
