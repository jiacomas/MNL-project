"""
Integration tests for user management system using mocks
"""

import unittest
from unittest.mock import patch

from backend.repositories.users_repo import UserRepository
from backend.schemas.users import Admin, Customers
from backend.services.users_service import UsersService


class TestUserManagementIntegration(unittest.TestCase):
    """Integration tests for complete user management cycle"""

    @patch('backend.repositories.users_repo.load_all')
    def setUp(self, mock_load):
        """Setup for each test"""
        mock_load.return_value = []

    @patch('backend.repositories.users_repo.save_all')
    @patch('uuid.uuid4')
    @patch('backend.repositories.users_repo.load_all')
    def test_create_and_save_admin_with_service(
        self, mock_load, mock_uuid, mock_save_all
    ):
        """Integration test: create admin using service and save"""
        mock_load.return_value = []
        mock_uuid.return_value.hex = "generated_id"

        repo = UserRepository("test_path.json")
        service = UsersService(repo)

        # Create admin through service
        admin = service.create_user(
            "admin1", "admin@test.com", "secret123", user_type="admin"
        )

        # Verify service called save
        mock_save_all.assert_called_once()

        # Verify data structure
        self.assertEqual(admin.username, "admin1")
        self.assertEqual(admin.email, "admin@test.com")
        self.assertIsInstance(admin, Admin)

    @patch('backend.repositories.users_repo.save_all')
    @patch('uuid.uuid4')
    @patch('backend.repositories.users_repo.load_all')
    def test_create_and_save_customer_with_service(
        self, mock_load, mock_uuid, mock_save_all
    ):
        """Integration test: create customer using service"""
        mock_load.return_value = []
        mock_uuid.return_value.hex = "generated_id"

        repo = UserRepository("test_path.json")
        service = UsersService(repo)

        # Create customer
        customer = service.create_user(
            "customer1",
            "customer@test.com",
            "pass456",
            user_type="customer",
            penalties="2",
            bookmarks=["item1", "item2"],
        )

        # Verify
        self.assertEqual(customer.username, "customer1")
        self.assertEqual(customer.penalties, "2")
        self.assertEqual(customer.bookmarks, ["item1", "item2"])
        mock_save_all.assert_called_once()

    @patch('backend.repositories.users_repo.save_all')
    @patch('uuid.uuid4')
    @patch('backend.repositories.users_repo.load_all')
    def test_create_multiple_users_workflow(self, mock_load, mock_uuid, mock_save_all):
        """Integration test: create multiple users through service"""
        mock_load.return_value = []
        mock_uuid.return_value.hex = "generated_id"

        repo = UserRepository("test_path.json")
        service = UsersService(repo)

        # Create various users
        admin = service.create_user(
            "admin1", "admin@test.com", "pass1", user_type="admin"
        )
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

        # Verify types
        self.assertIsInstance(admin, Admin)
        self.assertIsInstance(customer1, Customers)
        self.assertIsInstance(customer2, Customers)

        # Service should have called save 3 times
        self.assertEqual(mock_save_all.call_count, 3)

    @patch('backend.repositories.users_repo.save_all')
    @patch('backend.repositories.users_repo.load_all')
    def test_edit_user_workflow_with_service(self, mock_load, mock_save_all):
        """Integration test: edit user through service"""
        # Setup initial user
        admin = Admin(
            user_id="123",
            user_type="admin",
            username="admin1",
            email="old@test.com",
            password="pass",
            passwordHash="hash",
            admin_id="456",
        )
        mock_load.return_value = [admin]

        repo = UserRepository("test_path.json")
        service = UsersService(repo)

        # Edit user through service
        updated = service.edit_user_info("admin1", email="new@test.com")

        # Verify
        self.assertEqual(updated.email, "new@test.com")
        mock_save_all.assert_called_once()

    @patch('backend.repositories.users_repo.load_all')
    def test_remove_user_workflow(self, mock_load):
        """Integration test: remove users from repository"""
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

        mock_load.return_value = [admin, customer]

        repo = UserRepository("test_path.json")
        self.assertEqual(len(repo.users), 2)

        # Remove customer
        repo.users = [u for u in repo.users if u.username != "customer1"]

        # Verify removal
        self.assertEqual(len(repo.users), 1)
        self.assertEqual(repo.users[0].username, "admin1")

    @patch('backend.repositories.users_repo.load_all')
    def test_authentication_workflow_with_service(self, mock_load):
        """Integration test: complete authentication flow through service"""
        repo = UserRepository("test_path.json")
        service = UsersService(repo)

        password = "mySecretPass123"
        hashed = service.hash_password(password)  # SHA256 of password

        admin = Admin(
            user_id="123",
            user_type="admin",
            username="admin1",
            email="admin@test.com",
            password=password,
            passwordHash=hashed,
            admin_id="456",
        )

        mock_load.return_value = [admin]

        # Verify correct authentication
        self.assertTrue(service.check_password("admin1", password))

        # Verify incorrect authentication
        self.assertFalse(service.check_password("admin1", "wrongPassword"))

        # Verify non-existent user
        self.assertFalse(service.check_password("nonexistent", password))

    @patch('builtins.print')
    @patch('backend.repositories.users_repo.save_all')
    @patch('uuid.uuid4')
    @patch('backend.repositories.users_repo.load_all')
    def test_duplicate_username_handling_with_service(
        self, mock_load, mock_uuid, mock_save_all, mock_print
    ):
        """Integration test: handle duplicate usernames through service"""
        mock_load.return_value = []
        mock_uuid.return_value.hex = "generated_id"

        repo = UserRepository("test_path.json")
        service = UsersService(repo)

        # Create first user
        service.create_user("admin1", "admin1@test.com", "pass1", user_type="admin")

        # Try to create user with same username
        service.create_user("admin1", "admin2@test.com", "pass2", user_type="admin")

        # Should print warning
        mock_print.assert_called_with("Username already exists")

    @patch('backend.repositories.users_repo.save_all')
    @patch('backend.repositories.users_repo.load_all')
    def test_password_update_workflow(self, mock_load, mock_save_all):
        """Integration test: password update through repository"""
        password = "oldPass123"
        hashed = "hash_of_old_pass"

        admin = Admin(
            user_id="123",
            user_type="admin",
            username="admin1",
            email="admin@test.com",
            password=password,
            passwordHash=hashed,
            admin_id="456",
        )

        mock_load.return_value = [admin]

        repo = UserRepository("test_path.json")
        service = UsersService(repo)

        # Update password through direct manipulation (as in edit functions)
        user = repo.get_user_by_username("admin1")
        new_password = "newPass456"
        new_hash = service.hash_password(new_password)
        user.passwordHash = new_hash
        user.password = new_password

        # Verify new password
        self.assertFalse(service.check_password("admin1", password))
        self.assertTrue(service.check_password("admin1", new_password))

    @patch('backend.repositories.users_repo.save_all')
    @patch('backend.repositories.users_repo.load_all')
    def test_customer_bookmarks_workflow(self, mock_load, mock_save_all):
        """Integration test: customer bookmarks management"""
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

        mock_load.return_value = [customer]

        repo = UserRepository("test_path.json")

        # Add bookmarks
        user = repo.get_user_by_username("customer1")
        user.bookmarks.extend(["item1", "item2", "item3"])

        # Verify bookmarks
        self.assertEqual(len(user.bookmarks), 3)
        self.assertIn("item1", user.bookmarks)

    @patch('backend.repositories.users_repo.save_all')
    @patch('backend.repositories.users_repo.load_all')
    def test_penalties_management_workflow(self, mock_load, mock_save_all):
        """Integration test: penalties management through service"""
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

        mock_load.return_value = [customer]

        repo = UserRepository("test_path.json")
        service = UsersService(repo)

        # Increment penalties through service
        user = repo.get_user_by_username("customer1")
        current_penalties = int(user.penalties)
        service.edit_user_info("customer1", penalties=str(current_penalties + 1))

        # Verify penalties
        updated_user = repo.get_user_by_username("customer1")
        self.assertEqual(updated_user.penalties, "1")
        mock_save_all.assert_called_once()

    @patch('backend.repositories.users_repo.save_all')
    @patch('backend.repositories.users_repo.load_all')
    def test_user_type_update_workflow(self, mock_load, mock_save_all):
        """Integration test: update user type through service"""
        admin = Admin(
            user_id="123",
            user_type="admin",
            username="user1",
            email="user@test.com",
            password="pass",
            passwordHash="hash",
            admin_id="456",
        )

        mock_load.return_value = [admin]

        repo = UserRepository("test_path.json")
        service = UsersService(repo)

        # Update user type
        updated = service.edit_user_info("user1", user_type="customer")

        self.assertEqual(updated.user_type, "customer")
        mock_save_all.assert_called_once()

    @patch('backend.repositories.users_repo.save_all')
    @patch('backend.repositories.users_repo.load_all')
    def test_is_locked_functionality(self, mock_load, mock_save_all):
        """Integration test: user lock/unlock through service"""
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

        mock_load.return_value = [admin]

        repo = UserRepository("test_path.json")
        service = UsersService(repo)

        # Initially not locked
        self.assertFalse(admin.is_locked)

        # Lock user through service
        service.edit_user_info("admin1", is_locked=True)
        updated = repo.get_user_by_username("admin1")

        self.assertTrue(updated.is_locked)
        mock_save_all.assert_called_once()

    @patch('backend.repositories.users_repo.save_all')
    @patch('uuid.uuid4')
    @patch('backend.repositories.users_repo.load_all')
    def test_repository_save_called_on_create(
        self, mock_load, mock_uuid, mock_save_all
    ):
        """Integration test: verify repository.save() is called when creating users"""
        mock_load.return_value = []
        mock_uuid.return_value.hex = "generated_id"

        repo = UserRepository("test_path.json")
        service = UsersService(repo)

        service.create_user("admin1", "admin@test.com", "pass", user_type="admin")

        # Service should trigger repo.save() which calls save_all
        mock_save_all.assert_called_once_with(repo.users, path="test_path.json")


if __name__ == '__main__':
    unittest.main()
