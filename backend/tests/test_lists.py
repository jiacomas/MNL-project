import os

import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def setup_module(module):
    # Use a temporary file for tests
    os.environ["LISTS_PATH"] = "/tmp/test_lists.json"
    # Clear the file if it exists
    if os.path.exists("/tmp/test_lists.json"):
        os.remove("/tmp/test_lists.json")


def teardown_module(module):
    if os.path.exists("/tmp/test_lists.json"):
        os.remove("/tmp/test_lists.json")


@pytest.fixture
def cleanup_lists(jwt_user_headers):
    """Fixture to track and cleanup lists created during tests."""
    created_list_ids = []

    # Yield a helper function to track list IDs
    def track_list(list_id):
        created_list_ids.append(list_id)
        return list_id

    yield track_list

    # Cleanup: delete all tracked lists
    for list_id in created_list_ids:
        try:
            client.delete(f"/api/lists/{list_id}", headers=jwt_user_headers)
        except Exception:
            pass  # Ignore errors if list was already deleted


def test_create_list(jwt_user_headers, cleanup_lists):
    response = client.post(
        "/api/lists/",
        json={"name": "My Favorites", "description": "Best movies ever"},
        headers=jwt_user_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "My Favorites"
    assert data["description"] == "Best movies ever"
    assert "id" in data
    cleanup_lists(data["id"])


def test_list_my_lists(jwt_user_headers, cleanup_lists):
    # Ensure at least one list exists
    res = client.post(
        "/api/lists/", json={"name": "Watch Later"}, headers=jwt_user_headers
    )
    cleanup_lists(res.json()["id"])

    response = client.get("/api/lists/", headers=jwt_user_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(i["name"] == "Watch Later" for i in data)


def test_get_list(jwt_user_headers, cleanup_lists):
    # Create a list first
    create_res = client.post(
        "/api/lists/", json={"name": "To Get"}, headers=jwt_user_headers
    )
    list_id = cleanup_lists(create_res.json()["id"])

    response = client.get(f"/api/lists/{list_id}", headers=jwt_user_headers)
    assert response.status_code == 200
    assert response.json()["id"] == list_id


def test_update_list(jwt_user_headers, cleanup_lists):
    # Create a list
    create_res = client.post(
        "/api/lists/", json={"name": "Old Name"}, headers=jwt_user_headers
    )
    list_id = cleanup_lists(create_res.json()["id"])

    response = client.patch(
        f"/api/lists/{list_id}", json={"name": "New Name"}, headers=jwt_user_headers
    )
    assert response.status_code == 200
    assert response.json()["name"] == "New Name"


def test_add_remove_item(jwt_user_headers, cleanup_lists):
    # Create a list
    create_res = client.post(
        "/api/lists/", json={"name": "Movie List"}, headers=jwt_user_headers
    )
    list_id = cleanup_lists(create_res.json()["id"])
    movie_id = "tt1234567"

    # Add item
    add_res = client.post(
        f"/api/lists/{list_id}/items?movie_id={movie_id}",
        headers=jwt_user_headers,
    )
    assert add_res.status_code == 200
    assert movie_id in add_res.json()["items"]

    # Remove item
    del_res = client.delete(
        f"/api/lists/{list_id}/items/{movie_id}", headers=jwt_user_headers
    )
    assert del_res.status_code == 200
    assert movie_id not in del_res.json()["items"]


def test_delete_list(jwt_user_headers, cleanup_lists):
    # Create a list
    create_res = client.post(
        "/api/lists/", json={"name": "To Delete"}, headers=jwt_user_headers
    )
    list_id = cleanup_lists(create_res.json()["id"])

    # Delete it
    del_res = client.delete(f"/api/lists/{list_id}", headers=jwt_user_headers)
    assert del_res.status_code == 204

    # Verify it's gone
    get_res = client.get(f"/api/lists/{list_id}", headers=jwt_user_headers)
    assert get_res.status_code == 404


def test_bulk_operations_combined(jwt_user_headers, cleanup_lists):
    # Create a list with some items
    create_res = client.post(
        "/api/lists/", json={"name": "Combined Test"}, headers=jwt_user_headers
    )
    list_id = cleanup_lists(create_res.json()["id"])

    # Add initial items
    client.post(
        f"/api/lists/{list_id}/items?movie_id=movie1",
        headers=jwt_user_headers,
    )
    client.post(
        f"/api/lists/{list_id}/items?movie_id=movie2",
        headers=jwt_user_headers,
    )

    # Verify we have 2 items
    get_res = client.get(f"/api/lists/{list_id}", headers=jwt_user_headers)
    assert len(get_res.json()["items"]) == 2

    # Remove the old items and add new ones
    remove_res = client.post(
        f"/api/lists/{list_id}/items/bulk-remove",
        json=["movie1", "movie2"],
        headers=jwt_user_headers,
    )
    assert remove_res.status_code == 200
    assert len(remove_res.json()["items"]) == 0

    # Add new items
    add_res = client.post(
        f"/api/lists/{list_id}/items/bulk",
        json=["movie3", "movie4", "movie5"],
        headers=jwt_user_headers,
    )
    assert add_res.status_code == 200
    items = add_res.json()["items"]
    assert len(items) == 3
    assert "movie3" in items
    assert "movie4" in items
    assert "movie5" in items
    assert "movie1" not in items
    assert "movie2" not in items


def test_bulk_add_items(jwt_user_headers, cleanup_lists):
    # Create a list
    create_res = client.post(
        "/api/lists/", json={"name": "Bulk Add Test"}, headers=jwt_user_headers
    )
    list_id = cleanup_lists(create_res.json()["id"])

    # Bulk add items
    bulk_add_res = client.post(
        f"/api/lists/{list_id}/items/bulk",
        json=["movie1", "movie2", "movie3"],
        headers=jwt_user_headers,
    )
    assert bulk_add_res.status_code == 200
    items = bulk_add_res.json()["items"]
    assert len(items) == 3
    assert "movie1" in items
    assert "movie2" in items
    assert "movie3" in items

    # Add more items (should not duplicate)
    bulk_add_res2 = client.post(
        f"/api/lists/{list_id}/items/bulk",
        json=["movie2", "movie4"],
        headers=jwt_user_headers,
    )
    assert bulk_add_res2.status_code == 200
    items2 = bulk_add_res2.json()["items"]
    assert len(items2) == 4  # movie1, movie2, movie3, movie4
    assert items2.count("movie2") == 1  # No duplicates


def test_bulk_remove_items(jwt_user_headers, cleanup_lists):
    # Create a list with items
    create_res = client.post(
        "/api/lists/", json={"name": "Bulk Remove Test"}, headers=jwt_user_headers
    )
    list_id = cleanup_lists(create_res.json()["id"])

    # Add items
    client.post(
        f"/api/lists/{list_id}/items/bulk",
        json=["movie1", "movie2", "movie3", "movie4", "movie5"],
        headers=jwt_user_headers,
    )

    # Bulk remove items
    bulk_remove_res = client.post(
        f"/api/lists/{list_id}/items/bulk-remove",
        json=["movie2", "movie4"],
        headers=jwt_user_headers,
    )
    assert bulk_remove_res.status_code == 200
    items = bulk_remove_res.json()["items"]
    assert len(items) == 3
    assert "movie1" in items
    assert "movie3" in items
    assert "movie5" in items
    assert "movie2" not in items
    assert "movie4" not in items
