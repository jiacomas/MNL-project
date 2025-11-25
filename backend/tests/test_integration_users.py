"""
Integration-style tests for user management using UsersService + UsersRepo.

These tests use pytest + pytest-mock and heavily mock out filesystem
persistence (load_all / save_all) so that the workflows can be exercised
without touching real data files.
"""

from __future__ import annotations

import uuid

from backend.repositories.users_repo import UsersRepo
from backend.schemas.users import Admin, Customers
from backend.services.users_service import UsersService


def _make_service_with_mocks(mocker, initial_users=None):
    """Helper: create a UsersRepo + UsersService with load/save mocked."""
    if initial_users is None:
        initial_users = []

    load_all_mock = mocker.patch(
        "backend.repositories.users_repo.load_all",
        return_value=initial_users,
    )
    save_all_mock = mocker.patch("backend.repositories.users_repo.save_all")

    repo = UsersRepo()
    service = UsersService(repo)
    return repo, service, load_all_mock, save_all_mock


# ---------------------------------------------------------------------------
# User creation flows
# ---------------------------------------------------------------------------


def test_create_and_save_admin_with_service(mocker):
    """Integration-style test: create admin via service and persist."""
    # Arrange
    mocker.patch("uuid.uuid4", return_value=uuid.UUID(int=0))  # hex == "0" * 32
    repo, service, load_all_mock, save_all_mock = _make_service_with_mocks(mocker)

    # Act
    admin = service.create_user(
        username="admin1",
        email="admin@test.com",
        password="secret123",
        user_type="admin",
    )

    # Assert repo/save behaviour
    save_all_mock.assert_called_once()
    load_all_mock.assert_called_once()

    # Assert returned object
    assert isinstance(admin, Admin)
    assert admin.username == "admin1"
    assert admin.email == "admin@test.com"


def test_create_and_save_customer_with_service(mocker):
    """Integration-style test: create customer via service and persist."""
    mocker.patch("uuid.uuid4", return_value=uuid.UUID(int=0))
    repo, service, _, save_all_mock = _make_service_with_mocks(mocker)

    customer = service.create_user(
        username="customer1",
        email="customer@test.com",
        password="pass456",
        user_type="customer",
        penalties="2",
        bookmarks=["item1", "item2"],
    )

    assert isinstance(customer, Customers)
    assert customer.username == "customer1"
    assert customer.penalties == "2"
    assert customer.bookmarks == ["item1", "item2"]
    save_all_mock.assert_called_once()


def test_create_multiple_users_workflow(mocker):
    """Create several users via the service and verify types + save calls."""
    mocker.patch("uuid.uuid4", return_value=uuid.UUID(int=0))
    repo, service, _, save_all_mock = _make_service_with_mocks(mocker)

    admin = service.create_user("admin1", "admin@test.com", "pass1", user_type="admin")
    customer1 = service.create_user(
        "customer1",
        "c1@test.com",
        "pass2",
        user_type="customer",
        penalties="0",
        bookmarks=[],
    )
    customer2 = service.create_user(
        "customer2",
        "c2@test.com",
        "pass3",
        user_type="customer",
        penalties="1",
        bookmarks=["item1"],
    )

    assert isinstance(admin, Admin)
    assert isinstance(customer1, Customers)
    assert isinstance(customer2, Customers)

    # Each create triggers a save
    assert save_all_mock.call_count == 3


# ---------------------------------------------------------------------------
# Editing / removing users
# ---------------------------------------------------------------------------


def test_edit_user_workflow_with_service(mocker):
    """Edit an existing user via UsersService.edit_user_info."""
    admin = Admin(
        user_id="123",
        user_type="admin",
        username="admin1",
        email="old@test.com",
        password="pass",
        passwordHash="hash",
        admin_id="456",
    )

    repo, service, load_all_mock, save_all_mock = _make_service_with_mocks(
        mocker, initial_users=[admin]
    )

    updated = service.edit_user_info("admin1", email="new@test.com")

    assert updated.email == "new@test.com"
    save_all_mock.assert_called_once()
    load_all_mock.assert_called_once()


def test_remove_user_workflow(mocker):
    """Remove user directly from repo.users list (as original code did)."""
    admin = Admin(
        user_id="123",
        user_type="admin",
        username="admin1",
        email="admin@test.com",
        password="pass",
        passwordHash="hash",
        admin_id="456",
    )
    customer = Customers(
        user_id="789",
        user_type="customer",
        username="customer1",
        email="customer@test.com",
        password="pass",
        passwordHash="hash",
        customer_id="abc",
        penalties="0",
        bookmarks=[],
    )

    repo, _, _, _ = _make_service_with_mocks(mocker, initial_users=[admin, customer])

    assert len(repo.users) == 2

    # Remove customer
    repo.users = [u for u in repo.users if u.username != "customer1"]

    assert len(repo.users) == 1
    assert repo.users[0].username == "admin1"


def test_authentication_workflow_with_service(mocker):
    """Check full auth flow with correct/incorrect credentials."""
    # Hash password using service helper
    tmp_service = UsersService(UsersRepo())
    password = "mySecretPass123"
    hashed = tmp_service.hash_password(password)

    admin = Admin(
        user_id="123",
        user_type="admin",
        username="admin1",
        email="admin@test.com",
        password=password,
        passwordHash=hashed,
        admin_id="456",
    )

    repo, service, _, _ = _make_service_with_mocks(mocker, initial_users=[admin])

    assert service.check_password("admin1", password) is True
    assert service.check_password("admin1", "wrongPassword") is False
    assert service.check_password("nonexistent", password) is False


def test_duplicate_username_handling_with_service(mocker):
    """Creating a second user with same username prints a warning."""
    mocker.patch("uuid.uuid4", return_value=uuid.UUID(int=0))
    print_mock = mocker.patch("builtins.print")

    repo, service, _, _ = _make_service_with_mocks(mocker)

    service.create_user("admin1", "admin1@test.com", "pass1", user_type="admin")
    service.create_user("admin1", "admin2@test.com", "pass2", user_type="admin")

    print_mock.assert_called_with("Username already exists")


def test_password_update_workflow(mocker):
    """Update password by changing hash + value; verify check_password."""
    password = "oldPass123"
    old_hash = "hash_of_old_pass"

    admin = Admin(
        user_id="123",
        user_type="admin",
        username="admin1",
        email="admin@test.com",
        password=password,
        passwordHash=old_hash,
        admin_id="456",
    )

    repo, service, _, _ = _make_service_with_mocks(mocker, initial_users=[admin])

    # Directly manipulate stored user
    user = repo.get_user_by_username("admin1")
    new_password = "newPass456"
    new_hash = service.hash_password(new_password)
    user.passwordHash = new_hash
    user.password = new_password

    assert service.check_password("admin1", password) is False
    assert service.check_password("admin1", new_password) is True


# ---------------------------------------------------------------------------
# Domain workflows: bookmarks, penalties, lock state, user type
# ---------------------------------------------------------------------------


def test_customer_bookmarks_workflow(mocker):
    """Add bookmarks to a customer and verify their list."""
    customer = Customers(
        user_id="123",
        user_type="customer",
        username="customer1",
        email="customer@test.com",
        password="pass",
        passwordHash="hash",
        customer_id="456",
        penalties="0",
        bookmarks=[],
    )

    repo, _, _, _ = _make_service_with_mocks(mocker, initial_users=[customer])

    user = repo.get_user_by_username("customer1")
    user.bookmarks.extend(["item1", "item2", "item3"])

    assert len(user.bookmarks) == 3
    assert "item1" in user.bookmarks


def test_penalties_management_workflow(mocker):
    """Increment penalties for a customer via service.edit_user_info."""
    customer = Customers(
        user_id="123",
        user_type="customer",
        username="customer1",
        email="customer@test.com",
        password="pass",
        passwordHash="hash",
        customer_id="456",
        penalties="0",
        bookmarks=[],
    )

    repo, service, _, save_all_mock = _make_service_with_mocks(
        mocker, initial_users=[customer]
    )

    user = repo.get_user_by_username("customer1")
    current_penalties = int(user.penalties)

    service.edit_user_info("customer1", penalties=str(current_penalties + 1))

    updated_user = repo.get_user_by_username("customer1")
    assert updated_user.penalties == "1"
    save_all_mock.assert_called_once()


def test_user_type_update_workflow(mocker):
    """Change user_type via service.edit_user_info."""
    admin = Admin(
        user_id="123",
        user_type="admin",
        username="user1",
        email="user@test.com",
        password="pass",
        passwordHash="hash",
        admin_id="456",
    )

    repo, service, _, save_all_mock = _make_service_with_mocks(
        mocker, initial_users=[admin]
    )

    updated = service.edit_user_info("user1", user_type="customer")

    assert updated.user_type == "customer"
    save_all_mock.assert_called_once()


def test_is_locked_functionality(mocker):
    """Lock/unlock a user via edit_user_info."""
    admin = Admin(
        user_id="123",
        user_type="admin",
        username="admin1",
        email="admin@test.com",
        password="pass",
        passwordHash="hash",
        admin_id="456",
        is_locked=False,
    )

    repo, service, _, save_all_mock = _make_service_with_mocks(
        mocker, initial_users=[admin]
    )

    assert admin.is_locked is False

    service.edit_user_info("admin1", is_locked=True)
    updated = repo.get_user_by_username("admin1")

    assert updated.is_locked is True
    save_all_mock.assert_called_once()


def test_repository_save_called_on_create(mocker):
    """Verify repo.save() triggers save_all with the correct path."""
    mocker.patch("uuid.uuid4", return_value=uuid.UUID(int=0))
    load_all_mock = mocker.patch(
        "backend.repositories.users_repo.load_all",
        return_value=[],
    )
    save_all_mock = mocker.patch("backend.repositories.users_repo.save_all")

    repo = UsersRepo()
    service = UsersService(repo)

    service.create_user("admin1", "admin@test.com", "pass", user_type="admin")

    # load_all called once during repo initialization
    load_all_mock.assert_called_once()

    # Service should trigger repo.save() which delegates to save_all
    save_all_mock.assert_called_once_with(repo.users, path="backend/data/users.json")
