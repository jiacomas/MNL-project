import pytest
from unittest.mock import Mock, patch, MagicMock
from backend.services.auth_service import AuthService
from backend.repositories.items_repo import Repository

@pytest.fixture
def auth_service(self, mock_repository):
    service = AuthService(repository=mock_repository)
    return service

def test_user_not_found(self, auth_service, mock_repository):
    """
    user does not exist
    """
    # prepare the mocks
    mock_repository.find_by_username.return_value = None

    # execute the function
    result = auth_service.authenticate_user("nonexistent_user", "password123")

    # verifications
    assert "error" in result
    assert result["error"] == "User not found"
    mock_repository.find_by_username.assert_called_once_with("nonexistent_user")

def test_invalid_password_first_attempt(self, auth_service, mock_repository, sample_user):
    """
    user exists but password is incorrect (first attempt)
    """
    # prepare the mocks
    mock_repository.find_by_username.return_value = sample_user
    
    with patch('backend.services.auth_service.verify_password', return_value=False):
        with patch('backend.services.auth_service.increment_login_attempts', return_value=1):
            # execute the function
            result = auth_service.authenticate_user("testuser", "wrong_password")

            # verifications
            assert "error" in result
            assert result["error"] == "Invalid password"
            assert "Account locked" not in result["error"]  # no account lock message

def test_third_failed_attempt_locks_account(self, auth_service, mock_repository, sample_user):
    """
    user exists but password is incorrect (third attempt)
    """
    mock_repository.find_by_username.return_value = sample_user
    
    with patch('backend.services.auth_service.verify_password', return_value=False):
        with patch('backend.services.auth_service.increment_login_attempts', return_value=3):
            with patch('backend.services.auth_service.apply_account_lockout') as mock_lockout:
                # execute the function
                result = auth_service.authenticate_user("testuser", "wrong_password")

                # verifications 
                assert "error" in result
                assert result["error"] == "Account locked"
                mock_lockout.assert_called_once_with("testuser")

def test_locked_account_cannot_login(self, auth_service, mock_repository):
    """
    user exists but account is locked
    """
    # User with locked account
    locked_user = {
        "id": 2,
        "username": "locked_user",
        "password_hash": "$2b$12$hashed",
        "is_locked": True
    }
    mock_repository.find_by_username.return_value = locked_user
    
    with patch('backend.services.auth_service.verify_password', return_value=True):
        with patch('backend.services.auth_service.is_account_locked', return_value=True):
            # execute the function
            result = auth_service.authenticate_user("locked_user", "correct_password")

            # verifications
            assert "error" in result
            assert result["error"] == "Account is locked"

def test_successful_authentication(self, auth_service, mock_repository, sample_user):
    """
    user exists and password is correct
    """
    mock_repository.find_by_username.return_value = sample_user
    
    with patch('backend.services.auth_service.verify_password', return_value=True):
        with patch('backend.services.auth_service.is_account_locked', return_value=False):
            with patch('backend.services.auth_service.generate_jwt_token', return_value="mock.jwt.token"):
                with patch('backend.services.auth_service.reset_login_attempts') as mock_reset:
                    # execute the function
                    result = auth_service.authenticate_user("testuser", "correct_password")

                    # verifications
                    assert "token" in result
                    assert result["token"] == "mock.jwt.token"
                    assert result["user"]["username"] == "testuser"
                    mock_reset.assert_called_once_with("testuser")