import os

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


def test_create_list(jwt_user_headers):
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
    return data["id"]


def test_list_my_lists(jwt_user_headers):
    # Ensure at least one list exists
    client.post("/api/lists/", json={"name": "Watch Later"}, headers=jwt_user_headers)

    response = client.get("/api/lists/", headers=jwt_user_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(i["name"] == "Watch Later" for i in data)


def test_get_list(jwt_user_headers):
    # Create a list first
    create_res = client.post(
        "/api/lists/", json={"name": "To Get"}, headers=jwt_user_headers
    )
    list_id = create_res.json()["id"]

    response = client.get(f"/api/lists/{list_id}", headers=jwt_user_headers)
    assert response.status_code == 200
    assert response.json()["id"] == list_id


def test_update_list(jwt_user_headers):
    # Create a list
    create_res = client.post(
        "/api/lists/", json={"name": "Old Name"}, headers=jwt_user_headers
    )
    list_id = create_res.json()["id"]

    response = client.patch(
        f"/api/lists/{list_id}", json={"name": "New Name"}, headers=jwt_user_headers
    )
    assert response.status_code == 200
    assert response.json()["name"] == "New Name"


def test_add_remove_item(jwt_user_headers):
    # Create a list
    create_res = client.post(
        "/api/lists/", json={"name": "Movie List"}, headers=jwt_user_headers
    )
    list_id = create_res.json()["id"]
    movie_id = "tt1234567"

    # Add item
    add_res = client.post(
        f"/api/lists/{list_id}/items",
        json={"movie_id": movie_id},
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


def test_delete_list(jwt_user_headers):
    # Create a list
    create_res = client.post(
        "/api/lists/", json={"name": "To Delete"}, headers=jwt_user_headers
    )
    list_id = create_res.json()["id"]

    # Delete it
    del_res = client.delete(f"/api/lists/{list_id}", headers=jwt_user_headers)
    assert del_res.status_code == 204

    # Verify it's gone
    get_res = client.get(f"/api/lists/{list_id}", headers=jwt_user_headers)
    assert get_res.status_code == 404
