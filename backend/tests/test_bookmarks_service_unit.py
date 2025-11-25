import uuid

import pytest
from fastapi import HTTPException, status

from backend.schemas.bookmarks import BookmarkCreate, BookmarkOut
from backend.services import bookmarks_service as svc


# Helper: build a valid BookmarkOut instance
def _mk(id=None, user="u1", movie="m1"):
    """
    Create a BookmarkOut with a valid UUID id and ISO timestamps.
    If id is None, generate a fresh uuid4.
    """
    if id is None:
        id = uuid.uuid4()

    return BookmarkOut(
        id=id,  # can be uuid.UUID, Pydantic accepts it
        user_id=user,
        movie_id=movie,
        created_at="2025-01-01T00:00:00+00:00",
        updated_at="2025-01-01T00:00:00+00:00",
    )


# create_bookmark


def test_create_bookmark_success(mocker):
    """Should call repo.create when no duplicate exists."""
    mocker.patch.object(svc, "_repo")
    svc._repo.get_bookmarks_by_user.return_value = []

    created = _mk()
    svc._repo.create.return_value = created

    result = svc.create_bookmark(BookmarkCreate(movie_id="m1"), user_id="u1")

    svc._repo.create.assert_called_once()
    assert isinstance(result.id, uuid.UUID)
    assert result.movie_id == "m1"
    assert result.user_id == "u1"


def test_create_bookmark_duplicate(mocker):
    """Should reject duplicates."""
    mocker.patch.object(svc, "_repo")
    # service uses _find_for_user_and_movie via get_bookmarks_by_user
    svc._repo.get_bookmarks_by_user.return_value = [_mk(movie="m1")]

    with pytest.raises(HTTPException) as exc:
        svc.create_bookmark(BookmarkCreate(movie_id="m1"), user_id="u1")

    assert exc.value.status_code == status.HTTP_409_CONFLICT


# list_bookmarks


def test_list_bookmarks_all(mocker):
    """When user_id is None, list_all should be used."""
    mocker.patch.object(svc, "_repo")
    svc._repo.list_all.return_value = [_mk(), _mk()]

    result = svc.list_bookmarks(None)

    assert len(result) == 2
    svc._repo.list_all.assert_called_once()
    svc._repo.get_bookmarks_by_user.assert_not_called()


def test_list_bookmarks_for_user(mocker):
    """When user_id is provided, filter to that user."""
    mocker.patch.object(svc, "_repo")
    svc._repo.get_bookmarks_by_user.return_value = [_mk(user="u1")]

    result = svc.list_bookmarks("u1")

    assert len(result) == 1
    assert result[0].user_id == "u1"
    svc._repo.get_bookmarks_by_user.assert_called_once_with("u1")
    svc._repo.list_all.assert_not_called()


# count_bookmarks_for_movie


def test_list_bookmarks_for_movie(mocker):
    mocker.patch.object(svc, "_repo")
    svc._repo.get_bookmarks_by_movie.return_value = [_mk(movie="m1")]

    result = svc.list_bookmarks_for_movie("m1")

    assert result[0].movie_id == "m1"
    svc._repo.get_bookmarks_by_movie.assert_called_once_with("m1")


# get_user_bookmark


def test_get_user_bookmark(mocker):
    """Should return the bookmark for that (user, movie) pair."""
    mocker.patch.object(svc, "_repo")
    # service uses _find_for_user_and_movie → get_bookmarks_by_user
    svc._repo.get_bookmarks_by_user.return_value = [
        _mk(movie="m1"),
        _mk(movie="m2"),
    ]

    result = svc.get_user_bookmark("m1", "u1")

    assert result is not None
    assert result.movie_id == "m1"


def test_get_user_bookmark_none(mocker):
    """Return None if user has no bookmark for that movie."""
    mocker.patch.object(svc, "_repo")
    svc._repo.get_bookmarks_by_user.return_value = []

    result = svc.get_user_bookmark("m1", "u1")

    assert result is None


# delete_bookmark


def test_delete_bookmark_owner(mocker):
    """Owner can delete their own bookmark."""
    mocker.patch.object(svc, "_repo")
    bookmark_id = uuid.uuid4()

    svc._repo.list_all.return_value = [_mk(id=bookmark_id, user="u1")]
    svc._repo.delete.return_value = True

    svc.delete_bookmark(str(bookmark_id), user_id="u1", is_admin=False)

    svc._repo.delete.assert_called_once_with(str(bookmark_id))


def test_delete_bookmark_admin(mocker):
    """Admin may delete someone else's bookmark."""
    mocker.patch.object(svc, "_repo")
    bookmark_id = uuid.uuid4()

    svc._repo.list_all.return_value = [_mk(id=bookmark_id, user="u1")]
    svc._repo.delete.return_value = True

    svc.delete_bookmark(str(bookmark_id), user_id="admin", is_admin=True)

    svc._repo.delete.assert_called_once_with(str(bookmark_id))


def test_delete_bookmark_not_found(mocker):
    """404 when bookmark does not exist."""
    mocker.patch.object(svc, "_repo")
    bookmark_id = uuid.uuid4()

    svc._repo.list_all.return_value = []

    with pytest.raises(HTTPException) as exc:
        svc.delete_bookmark(str(bookmark_id), user_id="u1")

    assert exc.value.status_code == status.HTTP_404_NOT_FOUND
    svc._repo.delete.assert_not_called()


def test_delete_bookmark_unauthorized(mocker):
    """Non-owner non-admin should get 403."""
    mocker.patch.object(svc, "_repo")
    bookmark_id = uuid.uuid4()

    svc._repo.list_all.return_value = [_mk(id=bookmark_id, user="u1")]

    with pytest.raises(HTTPException) as exc:
        svc.delete_bookmark(str(bookmark_id), user_id="u2", is_admin=False)

    assert exc.value.status_code == status.HTTP_403_FORBIDDEN
    svc._repo.delete.assert_not_called()


# export_bookmarks


def test_export_bookmarks(mocker):
    mocker.patch.object(svc, "_repo")
    svc._repo.export_to_csv.return_value = "/tmp/bookmarks_export.csv"

    result = svc.export_bookmarks()

    assert result == "/tmp/bookmarks_export.csv"
    svc._repo.export_to_csv.assert_called_once()
