"""
Unit tests for UsersService using mocks
"""

import unittest
from unittest.mock import Mock, patch

from backend.repositories.users_repo import UserRepository
from backend.schemas.users import Admin, Customers

# import global salted hashing
from backend.services.password_reset_service import verify_password as global_verify
from backend.services.users_service import UsersService


class TestUsersService(unittest.TestCase):
    """Unit tests for UsersService class"""

    def setUp(self):
        """Setup for each test"""
        self.mock_repo = Mock(spec=UserRepository)
        self.mock_repo.users = []
        self.mock_repo.file_path = "test_path.json"
        self.service = UsersService(self.mock_repo)

    def test_hash_password(self):
        """Test password hashing"""
        password = "test123"
        hashed = self.service.hash_password(password)

        self.assertIn("$", hashed)  # must contain salt
        self.assertEqual(len(hashed.split("$")), 2)

    def test_hash_password_consistency(self):
        """Test that password hashing is consistent"""
        password = "test123"
        hash1 = self.service.hash_password(password)
        hash2 = self.service.hash_password(password)

        self.assertNotEqual(hash1, hash2)  # salted hashes differ
        self.assertTrue(global_verify(password, hash1))
        self.assertTrue(global_verify(password, hash2))

    def test_check_password_valid(self):
        """Test valid password verification"""
        password = "test123"
        hashed = self.service.hash_password(password)

        admin = Admin(
            user_id="123",
            user_type="admin",
            username="testuser",
            email="test@test.com",
            password=password,
            passwordHash=hashed,
            admin_id="456",
        )

        self.mock_repo.get_user_by_username.return_value = admin

        result = self.service.check_password("testuser", password)

        self.assertTrue(result)
        self.mock_repo.get_user_by_username.assert_called_once_with("testuser")

    def test_check_password_invalid(self):
        """Test invalid password verification"""
        password = "test123"
        wrong_password = "wrong123"
        hashed = self.service.hash_password(password)

        admin = Admin(
            user_id="123",
            user_type="admin",
            username="testuser",
            email="test@test.com",
            password=password,
            passwordHash=hashed,
            admin_id="456",
        )

        self.mock_repo.get_user_by_username.return_value = admin

        result = self.service.check_password("testuser", wrong_password)

        self.assertFalse(result)

    def test_check_password_user_not_found(self):
        """Test password check when user doesn't exist"""
        self.mock_repo.get_user_by_username.return_value = None

        result = self.service.check_password("nonexistent", "password")

        self.assertFalse(result)

    def test_check_password_no_password_hash(self):
        """Test password check when user has no password hash"""
        user = Mock()
        user.passwordHash = None

        self.mock_repo.get_user_by_username.return_value = user

        result = self.service.check_password("testuser", "password")

        self.assertFalse(result)

    @patch('uuid.uuid4')
    def test_create_admin(self, mock_uuid):
        """Test admin creation"""
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
        self.assertNotEqual(admin.passwordHash, "pass123")  # Should be hashed
        self.mock_repo.save.assert_called_once()

    @patch('uuid.uuid4')
    def test_create_customer(self, mock_uuid):
        """Test customer creation"""
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

    @patch('uuid.uuid4')
    def test_create_customer_with_defaults(self, mock_uuid):
        """Test customer creation with default values"""
        mock_uuid.return_value.hex = "generated_id"
        self.mock_repo.user_exists.return_value = False
        self.mock_repo.username_exists.return_value = False

        customer = self.service.create_user(
            "customer1", "customer@test.com", "pass123", user_type="customer"
        )

        self.assertEqual(customer.penalties, "")
        self.assertEqual(customer.bookmarks, [])

    def test_create_user_invalid_type(self):
        """Test creating user with invalid type"""
        self.mock_repo.user_exists.return_value = False
        self.mock_repo.username_exists.return_value = False

        with self.assertRaises(ValueError) as context:
            self.service.create_user(
                "test", "test@test.com", "pass", user_type="invalid"
            )

        self.assertIn("Invalid user type", str(context.exception))

    @patch('builtins.print')
    @patch('uuid.uuid4')
    def test_create_user_duplicate_username(self, mock_uuid, mock_print):
        """Test creating user with duplicate username prints warning"""
        mock_uuid.return_value.hex = "generated_id"
        self.mock_repo.user_exists.return_value = False
        self.mock_repo.username_exists.return_value = True

        self.service.create_user("existing", "test@test.com", "pass", user_type="admin")

        mock_print.assert_called_with("Username already exists")

    @patch('builtins.print')
    @patch('uuid.uuid4')
    def test_create_user_duplicate_user_id(self, mock_uuid, mock_print):
        """Test creating user with duplicate user_id prints warning"""
        mock_uuid.return_value.hex = "generated_id"
        self.mock_repo.user_exists.return_value = True
        self.mock_repo.username_exists.return_value = False

        self.service.create_user(
            "newuser", "test@test.com", "pass", user_type="admin", user_id="existing_id"
        )

        mock_print.assert_called_with("User ID already exists")

    @patch('uuid.uuid4')
    def test_create_user_with_specific_ids(self, mock_uuid):
        """Test creating user with specific IDs"""
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

    @patch('uuid.uuid4')
    def test_create_user_with_is_locked(self, mock_uuid):
        """Test creating locked user"""
        mock_uuid.return_value.hex = "generated_id"
        self.mock_repo.user_exists.return_value = False
        self.mock_repo.username_exists.return_value = False

        admin = self.service.create_user(
            "admin1", "admin@test.com", "pass", user_type="admin", is_locked=True
        )

        self.assertTrue(admin.is_locked)

    def test_edit_user_info(self):
        """Test editing user information"""
        admin = Admin(
            user_id="123",
            user_type="admin",
            username="admin1",
            email="old@test.com",
            password="pass",
            passwordHash="hash",
            admin_id="456",
        )

        self.mock_repo.get_user_by_username.return_value = admin

        updated = self.service.edit_user_info("admin1", email="new@test.com")

        self.assertEqual(updated.email, "new@test.com")
        self.mock_repo.save.assert_called_once()

    def test_edit_user_info_multiple_fields(self):
        """Test editing multiple fields"""
        customer = Customers(
            user_id="123",
            user_type="customer",
            username="customer1",
            email="old@test.com",
            password="pass",
            passwordHash="hash",
            customer_id="456",
            penalties="0",
            bookmarks=[],
        )

        self.mock_repo.get_user_by_username.return_value = customer

        updated = self.service.edit_user_info(
            "customer1", email="new@test.com", penalties="2"
        )

        self.assertEqual(updated.email, "new@test.com")
        self.assertEqual(updated.penalties, "2")

    def test_edit_user_info_not_found(self):
        """Test editing non-existent user"""
        self.mock_repo.get_user_by_username.return_value = None

        with self.assertRaises(ValueError) as context:
            self.service.edit_user_info("nonexistent", email="test@test.com")

        self.assertIn("User not found", str(context.exception))

    def test_edit_user_info_invalid_field(self):
        """Test editing with invalid field (should be ignored)"""
        admin = Admin(
            user_id="123",
            user_type="admin",
            username="admin1",
            email="admin@test.com",
            password="pass",
            passwordHash="hash",
            admin_id="456",
        )

        self.mock_repo.get_user_by_username.return_value = admin

        # Try to set a field that doesn't exist
        updated = self.service.edit_user_info("admin1", nonexistent_field="value")

        # Should not raise error, just ignore the field
        self.assertFalse(hasattr(updated, "nonexistent_field"))

    @patch('uuid.uuid4')
    def test_password_is_hashed_on_creation(self, mock_uuid):
        """Test that password is hashed when creating user"""
        mock_uuid.return_value.hex = "generated_id"
        self.mock_repo.user_exists.return_value = False
        self.mock_repo.username_exists.return_value = False

        plain_password = "plaintext123"
        admin = self.service.create_user(
            "admin1", "admin@test.com", plain_password, user_type="admin"
        )

        self.assertNotEqual(admin.passwordHash, plain_password)
        self.assertTrue(global_verify(plain_password, admin.passwordHash))


if __name__ == '__main__':
    unittest.main()
