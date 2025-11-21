from uuid import uuid4

from .conftest import now_iso


# ---- Helpers ----
def mk(uuid=None, user="u1", movie="m1"):
    return {
        "id": uuid or str(uuid4()),
        "user_id": user,
        "movie_id": movie,
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }


# ---- Tests ----


def test_list_bookmarks(client, mock_bookmarks_service, jwt_user_headers):
    bid = str(uuid4())
    mock_bookmarks_service.list_bookmarks.return_value = [mk(bid)]

    r = client.get("/api/bookmarks", headers=jwt_user_headers)
    assert r.status_code == 200
    mock_bookmarks_service.list_bookmarks.assert_called_once_with("u1")


def test_list_bookmarks_for_movie_admin(
    client, mock_bookmarks_service, jwt_admin_headers
):
    mock_bookmarks_service.list_bookmarks_for_movie.return_value = [
        {
            "id": str(uuid4()),
            "user_id": "u1",
            "movie_id": "m1",
            "created_at": now_iso(),
            "updated_at": now_iso(),
        }
    ]
    r = client.get("/api/bookmarks/movie/m1", headers=jwt_admin_headers)
    assert r.status_code == 200
    mock_bookmarks_service.list_bookmarks_for_movie.assert_called_once_with("m1")


def test_list_bookmarks_for_movie_forbidden(client, jwt_user_headers):
    r = client.get("/api/bookmarks/movie/m1", headers=jwt_user_headers)
    assert r.status_code == 403


def test_count_bookmarks(client, mock_bookmarks_service):
    mock_bookmarks_service.count_bookmarks_for_movie.return_value = 8
    r = client.get("/api/bookmarks/movie/m1/users/count")
    assert r.status_code == 200
    assert r.json()["count"] == 8


def test_create_bookmark(client, mock_bookmarks_service, jwt_user_headers):
    bid = str(uuid4())
    mock_bookmarks_service.create_bookmark.return_value = mk(bid)

    r = client.post("/api/bookmarks", json={"movie_id": "m1"}, headers=jwt_user_headers)
    assert r.status_code in (200, 201)

    args, kwargs = mock_bookmarks_service.create_bookmark.call_args
    assert args[1] == "u1"  # user passed in
    assert getattr(args[0], "movie_id") == "m1"  # model parsed


def test_get_my_bookmark(client, mock_bookmarks_service, jwt_user_headers):
    bid = str(uuid4())
    mock_bookmarks_service.get_user_bookmark.return_value = mk(bid)

    r = client.get("/api/bookmarks/me?movie_id=m1", headers=jwt_user_headers)
    assert r.status_code == 200

    mock_bookmarks_service.get_user_bookmark.assert_called_once_with("m1", "u1")


def test_delete_my_bookmark(client, mock_bookmarks_service, jwt_user_headers):
    bid = str(uuid4())
    r = client.delete(f"/api/bookmarks/me/{bid}", headers=jwt_user_headers)
    assert r.status_code in (200, 204)

    mock_bookmarks_service.delete_bookmark.assert_called_once_with(bid, "u1", False)


def test_delete_bookmark_admin(client, mock_bookmarks_service, jwt_admin_headers):
    bid = str(uuid4())
    r = client.delete(f"/api/bookmarks/{bid}", headers=jwt_admin_headers)
    assert r.status_code in (200, 204)

    mock_bookmarks_service.delete_bookmark.assert_called_once_with(bid, "admin", True)


def test_export_bookmarks(client, mock_bookmarks_service, jwt_admin_headers):
    mock_bookmarks_service.export_bookmarks.return_value = "/tmp/bookmarks.csv"

    r = client.get("/api/bookmarks/export", headers=jwt_admin_headers)
    assert r.status_code == 200
    mock_bookmarks_service.export_bookmarks.assert_called_once()


def test_export_forbidden_user(client, jwt_user_headers):
    r = client.get("/api/bookmarks/export", headers=jwt_user_headers)
    assert r.status_code == 403
