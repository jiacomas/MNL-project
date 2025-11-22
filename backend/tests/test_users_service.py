"""
Unit tests for UsersService using mocks.
"""

from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from backend.repositories.users_repo import UserRepository
from backend.schemas.users import Admin, Customers
from backend.services.password_reset_service import verify_password as global_verify
from backend.services.users_service import UsersService


class TestUsersService(unittest.TestCase):
    """Unit tests for UsersService."""

    def setUp(self) -> None:
        """Create a mocked UserRepository and service for each test."""
        self.mock_repo: UserRepository = Mock(spec=UserRepository)
        self.mock_repo.users = []
        self.mock_repo.file_path = "test_path.json"
        self.service = UsersService(self.mock_repo)

    # ------------------------------------------------------------------
    # Helper builders
    # ------------------------------------------------------------------

    def _make_admin(
        self,
        username: str = "admin1",
        email: str = "admin@test.com",
        password: str = "pass",
        password_hash: str = "hash",
        user_id: str = "123",
        admin_id: str = "456",
        is_locked: bool = False,
    ) -> Admin:
        return Admin(
            user_id=user_id,
            user_type="admin",
            username=username,
            email=email,
            password=password,
            passwordHash=password_hash,
            admin_id=admin_id,
            is_locked=is_locked,
        )

    def _make_customer(
        self,
        username: str = "customer1",
        email: str = "customer@test.com",
        password: str = "pass",
        password_hash: str = "hash",
        user_id: str = "123",
        customer_id: str = "456",
        penalties: str = "0",
        bookmarks: list[str] | None = None,
    ) -> Customers:
        return Customers(
            user_id=user_id,
            user_type="customer",
            username=username,
            email=email,
            password=password,
            passwordHash=password_hash,
            customer_id=customer_id,
            penalties=penalties,
            bookmarks=bookmarks or [],
        )

    # ------------------------------------------------------------------
    # Password hashing & verification
    # ------------------------------------------------------------------

    def test_hash_password(self) -> None:
        """Password hashing should include a salt and delimiter."""
        password = "test123"
        hashed = self.service.hash_password(password)

        self.assertIn("$", hashed)
        self.assertEqual(len(hashed.split("$")), 2)

    def test_hash_password_consistency(self) -> None:
        """Hashing the same password twice should produce different salted hashes."""
        password = "test123"
        hash1 = self.service.hash_password(password)
        hash2 = self.service.hash_password(password)

        self.assertNotEqual(hash1, hash2)
        self.assertTrue(global_verify(password, hash1))
        self.assertTrue(global_verify(password, hash2))

    def test_check_password_valid(self) -> None:
        """Valid password should pass verification."""
        password = "test123"
        hashed = self.service.hash_password(password)

        admin = self._make_admin(
            username="testuser",
            email="test@test.com",
            password=password,
            password_hash=hashed,
        )
        self.mock_repo.get_user_by_username.return_value = admin

        result = self.service.check_password("testuser", password)

        self.assertTrue(result)
        self.mock_repo.get_user_by_username.assert_called_once_with("testuser")

    def test_check_password_invalid(self) -> None:
        """Invalid password should fail verification."""
        password = "test123"
        wrong_password = "wrong123"
        hashed = self.service.hash_password(password)

        admin = self._make_admin(
            username="testuser",
            email="test@test.com",
            password=password,
            password_hash=hashed,
        )
        self.mock_repo.get_user_by_username.return_value = admin

        result = self.service.check_password("testuser", wrong_password)

        self.assertFalse(result)

    def test_check_password_user_not_found(self) -> None:
        """Password check for a non-existent user should return False."""
        self.mock_repo.get_user_by_username.return_value = None

        result = self.service.check_password("nonexistent", "password")

        self.assertFalse(result)

    def test_check_password_no_password_hash(self) -> None:
        """Password check should fail when user has no passwordHash stored."""
        user = Mock()
        user.passwordHash = None
        self.mock_repo.get_user_by_username.return_value = user

        result = self.service.check_password("testuser", "password")

        self.assertFalse(result)

    # ------------------------------------------------------------------
    # User creation
    # ------------------------------------------------------------------

    @patch("uuid.uuid4")
    def test_create_admin(self, mock_uuid) -> None:
        """Creating an admin should produce an Admin instance and save via repo."""
        mock_uuid.return_value.hex = "generated_id"
        self.mock_repo.user_exists.return_value = False
        self.mock_repo.username_exists.return_value = False

        admin = self.service.create_user(
            "admin1", "admin@test.com", "pass123", user_type="admin"
        )

        self.assertIsInstance(admin, Admin)
        self.assertEqual(admin.username, "admin1")
        self.assertEqual(admin.email, "admin@test.com")
        self.assertEqual(admin.user_type, "admin")
        self.assertNotEqual(admin.passwordHash, "pass123")
        self.mock_repo.save.assert_called_once()

    @patch("uuid.uuid4")
    def test_create_customer(self, mock_uuid) -> None:
        """Creating a customer should produce a Customers instance and save."""
        mock_uuid.return_value.hex = "generated_id"
        self.mock_repo.user_exists.return_value = False
        self.mock_repo.username_exists.return_value = False

        customer = self.service.create_user(
            "customer1",
            "customer@test.com",
            "pass123",
            user_type="customer",
            penalties="2",
            bookmarks=["item1"],
        )

        self.assertIsInstance(customer, Customers)
        self.assertEqual(customer.username, "customer1")
        self.assertEqual(customer.penalties, "2")
        self.assertEqual(customer.bookmarks, ["item1"])
        self.mock_repo.save.assert_called_once()

    @patch("uuid.uuid4")
    def test_create_customer_with_defaults(self, mock_uuid) -> None:
        """Customer creation without explicit penalties/bookmarks uses defaults."""
        mock_uuid.return_value.hex = "generated_id"
        self.mock_repo.user_exists.return_value = False
        self.mock_repo.username_exists.return_value = False

        customer = self.service.create_user(
            "customer1", "customer@test.com", "pass123", user_type="customer"
        )

        self.assertEqual(customer.penalties, "")
        self.assertEqual(customer.bookmarks, [])

    def test_create_user_invalid_type(self) -> None:
        """Invalid user_type should raise ValueError."""
        self.mock_repo.user_exists.return_value = False
        self.mock_repo.username_exists.return_value = False

        with self.assertRaises(ValueError) as ctx:
            self.service.create_user(
                "test", "test@test.com", "pass", user_type="invalid"
            )

        self.assertIn("Invalid user type", str(ctx.exception))

    @patch("builtins.print")
    @patch("uuid.uuid4")
    def test_create_user_duplicate_username(self, mock_uuid, mock_print) -> None:
        """Creating a user with duplicate username prints a warning."""
        mock_uuid.return_value.hex = "generated_id"
        self.mock_repo.user_exists.return_value = False
        self.mock_repo.username_exists.return_value = True

        self.service.create_user("existing", "test@test.com", "pass", user_type="admin")

        mock_print.assert_called_with("Username already exists")

    @patch("builtins.print")
    @patch("uuid.uuid4")
    def test_create_user_duplicate_user_id(self, mock_uuid, mock_print) -> None:
        """Creating a user with an existing user_id prints a warning."""
        mock_uuid.return_value.hex = "generated_id"
        self.mock_repo.user_exists.return_value = True
        self.mock_repo.username_exists.return_value = False

        self.service.create_user(
            "newuser", "test@test.com", "pass", user_type="admin", user_id="existing_id"
        )

        mock_print.assert_called_with("User ID already exists")

    @patch("uuid.uuid4")
    def test_create_user_with_specific_ids(self, mock_uuid) -> None:
        """create_user should respect explicitly provided user_id/admin_id."""
        mock_uuid.return_value.hex = "generated_id"
        self.mock_repo.user_exists.return_value = False
        self.mock_repo.username_exists.return_value = False

        admin = self.service.create_user(
            "admin1",
            "admin@test.com",
            "pass",
            user_type="admin",
            user_id="custom_user_id",
            admin_id="custom_admin_id",
        )

        self.assertEqual(admin.user_id, "custom_user_id")
        self.assertEqual(admin.admin_id, "custom_admin_id")

    @patch("uuid.uuid4")
    def test_create_user_with_is_locked(self, mock_uuid) -> None:
        """create_user should allow creating a locked user."""
        mock_uuid.return_value.hex = "generated_id"
        self.mock_repo.user_exists.return_value = False
        self.mock_repo.username_exists.return_value = False

        admin = self.service.create_user(
            "admin1", "admin@test.com", "pass", user_type="admin", is_locked=True
        )

        self.assertTrue(admin.is_locked)

    @patch("uuid.uuid4")
    def test_password_is_hashed_on_creation(self, mock_uuid) -> None:
        """Password must be hashed when creating a user."""
        mock_uuid.return_value.hex = "generated_id"
        self.mock_repo.user_exists.return_value = False
        self.mock_repo.username_exists.return_value = False

        plain_password = "plaintext123"
        admin = self.service.create_user(
            "admin1", "admin@test.com", plain_password, user_type="admin"
        )

        self.assertNotEqual(admin.passwordHash, plain_password)
        self.assertTrue(global_verify(plain_password, admin.passwordHash))

    # ------------------------------------------------------------------
    # Edit user info
    # ------------------------------------------------------------------

    def test_edit_user_info(self) -> None:
        """Editing a user updates fields and triggers repo.save()."""
        admin = self._make_admin(email="old@test.com")
        self.mock_repo.get_user_by_username.return_value = admin

        updated = self.service.edit_user_info("admin1", email="new@test.com")

        self.assertEqual(updated.email, "new@test.com")
        self.mock_repo.save.assert_called_once()

    def test_edit_user_info_multiple_fields(self) -> None:
        """Multiple editable fields should be updated in one call."""
        customer = self._make_customer(
            email="old@test.com",
            penalties="0",
            bookmarks=[],
        )
        self.mock_repo.get_user_by_username.return_value = customer

        updated = self.service.edit_user_info(
            "customer1", email="new@test.com", penalties="2"
        )

        self.assertEqual(updated.email, "new@test.com")
        self.assertEqual(updated.penalties, "2")

    def test_edit_user_info_not_found(self) -> None:
        """Editing a non-existent user should raise ValueError."""
        self.mock_repo.get_user_by_username.return_value = None

        with self.assertRaises(ValueError) as ctx:
            self.service.edit_user_info("nonexistent", email="test@test.com")

        self.assertIn("User not found", str(ctx.exception))

    def test_edit_user_info_invalid_field(self) -> None:
        """Unknown fields in kwargs should be ignored silently."""
        admin = self._make_admin()
        self.mock_repo.get_user_by_username.return_value = admin

        updated = self.service.edit_user_info("admin1", nonexistent_field="value")

        self.assertFalse(hasattr(updated, "nonexistent_field"))


if __name__ == "__main__":
    unittest.main()
