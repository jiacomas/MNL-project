# bandit: skip B101

import json
from unittest.mock import patch

import pytest
from repositories.users_repo import UserRepository
from services.users_service import AuthService


@pytest.fixture
def user_repository(temp_data_dir):
    """create real repository pointing to a temp file"""
    users_file = temp_data_dir / "users.json"
    # initialize the file with an empty structure
    with open(users_file, 'w') as f:
        json.dump({"users": []}, f)
    return UserRepository(str(users_file))


def auth_service(user_repository):
    service = AuthService(repository=user_repository)
    return service


def test_user_not_found(auth_service, user_repository):
    """
    user does not exist
    """
    # prepare the mocks
    user_repository.find_by_username.return_value = None

    # execute the function
    result = auth_service.authenticate_user("nonexistent_user", "password123")

    # verifications
    assert "error" in result  # nosec B101
    assert result["error"] == "User not found"  # nosec B101
    user_repository.find_by_username.assert_called_once_with("nonexistent_user")


def test_invalid_password_first_attempt(auth_service, user_repository, sample_user):
    """
    user exists but password is incorrect (first attempt)
    """
    # prepare the mocks
    user_repository.find_by_username.return_value = sample_user

    with patch('backend.services.auth_service.verify_password', return_value=False):
        with patch(
            'backend.services.auth_service.increment_login_attempts', return_value=1
        ):
            # execute the function
            result = auth_service.authenticate_user("testuser", "wrong_password")

            # verifications
            assert "error" in result  # nosec B101
            assert result["error"] == "Invalid password"  # nosec B101
            assert (
                "Account locked" not in result["error"]
            )  # no account lock message # nosec B101


def test_third_failed_attempt_locks_account(auth_service, user_repository, sample_user):
    """
    user exists but password is incorrect (third attempt)
    """
    user_repository.find_by_username.return_value = sample_user

    with patch('backend.services.auth_service.verify_password', return_value=False):
        with patch(
            'backend.services.auth_service.increment_login_attempts', return_value=3
        ):
            with patch(
                'backend.services.auth_service.apply_account_lockout'
            ) as mock_lockout:
                # execute the function
                result = auth_service.authenticate_user("testuser", "wrong_password")

                # verifications
                assert "error" in result  # nosec B101
                assert result["error"] == "Account locked"  # nosec B101
                mock_lockout.assert_called_once_with("testuser")


def test_locked_account_cannot_login(auth_service, user_repository):
    """
    user exists but account is locked
    """
    # User with locked account
    locked_user = {
        "id": 2,
        "username": "locked_user",
        "password_hash": "$2b$12$hashed",
        "is_locked": True,
    }
    user_repository.find_by_username.return_value = locked_user

    with patch('backend.services.auth_service.verify_password', return_value=True):
        with patch(
            'backend.services.auth_service.is_account_locked', return_value=True
        ):
            # execute the function
            result = auth_service.authenticate_user("locked_user", "correct_password")

            # verifications
            assert "error" in result  # nosec B101
            assert result["error"] == "Account is locked"  # nosec B101


def test_successful_authentication(auth_service, user_repository, sample_user):
    """
    user exists and password is correct
    """
    user_repository.find_by_username.return_value = sample_user

    with patch('backend.services.auth_service.verify_password', return_value=True):
        with patch(
            'backend.services.auth_service.is_account_locked', return_value=False
        ):
            with patch(
                'backend.services.auth_service.generate_jwt_token',
                return_value="mock.jwt.token",
            ):
                with patch(
                    'backend.services.auth_service.reset_login_attempts'
                ) as mock_reset:
                    # execute the function
                    result = auth_service.authenticate_user(
                        "testuser", "correct_password"
                    )

                    # verifications
                    assert "token" in result  # nosec B101
                    assert result["token"] == "mock.jwt.token"  # nosec B101
                    assert result["user"]["username"] == "testuser"  # nosec B101
                    mock_reset.assert_called_once_with("testuser")
