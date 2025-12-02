# backend/tests/test_admin_sync_router_unit.py


def test_load_kaggle_requires_admin(client, jwt_user_headers):
    """
    Non-admin users should not be allowed to call /admin/load-kaggle.
    We expect 401 or 403 depending on your auth implementation.
    """
    resp = client.post("/admin/load-kaggle", headers=jwt_user_headers)
    assert resp.status_code in (401, 403)


def test_load_kaggle_success_for_admin(client, jwt_admin_headers, mocker):
    """
    Admin can call /admin/load-kaggle, and the endpoint should call
    data_loader.load_movies_from_kaggle and return its summary.
    """
    # Arrange: patch load_movies_from_kaggle on the router module
    fake_summary = {
        "files_copied": 3,
        "target_root": "/fake/path",
    }

    fake_loader = mocker.patch(
        "backend.routers.admin_sync.load_movies_from_kaggle",
        return_value=fake_summary,
    )

    # Act
    resp = client.post("/admin/load-kaggle", headers=jwt_admin_headers)

    # Assert
    assert resp.status_code == 200
    data = resp.json()

    # The endpoint should have been called exactly once
    fake_loader.assert_called_once()

    # Response should contain the merged summary and a detail message
    assert data["detail"] == "Kaggle movies dataset loaded successfully."
    assert data["files_copied"] == 3
    assert data["target_root"] == "/fake/path"
