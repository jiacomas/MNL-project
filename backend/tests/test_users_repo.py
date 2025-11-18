"""
Unit tests for UserRepository using mocks
"""

import unittest
from unittest.mock import mock_open, patch

from backend.repositories.users_repo import UserRepository, load_all, save_all
from backend.schemas.users import Admin, Customers


class TestLoadAll(unittest.TestCase):
    """Unit tests for load_all function"""

    @patch('os.path.exists')
    def test_load_all_file_not_exists(self, mock_exists):
        """Test when file doesn't exist"""
        mock_exists.return_value = False

        result = load_all("non_existent_file.json")

        self.assertEqual(result, [])
        mock_exists.assert_called_once_with("non_existent_file.json")

    @patch(
        'builtins.open',
        new_callable=mock_open,
        read_data='[{"user_id": "123", "user_type": "admin", "username": "admin1", '
        '"email": "admin@test.com", "password": "pass", "passwordHash": "hash123", '
        '"is_locked": false, "admin_id": "456"}]',
    )
    @patch('os.path.exists')
    def test_load_all_with_admin(self, mock_exists, mock_file):
        """Test loading an admin user"""
        mock_exists.return_value = True

        users = load_all("test_path.json")

        self.assertEqual(len(users), 1)
        self.assertIsInstance(users[0], Admin)
        self.assertEqual(users[0].username, "admin1")
        self.assertEqual(users[0].admin_id, "456")

    @patch(
        'builtins.open',
        new_callable=mock_open,
        read_data='[{"user_id": "789", "user_type": "customer", "username": "customer1", '
        '"email": "customer@test.com", "password": "pass", "passwordHash": "hash456", '
        '"is_locked": false, "customer_id": "abc", "penalties": "0", "bookmarks": ["item1"]}]',
    )
    @patch('os.path.exists')
    def test_load_all_with_customer(self, mock_exists, mock_file):
        """Test loading a customer user"""
        mock_exists.return_value = True

        users = load_all("test_path.json")

        self.assertEqual(len(users), 1)
        self.assertIsInstance(users[0], Customers)
        self.assertEqual(users[0].username, "customer1")
        self.assertEqual(users[0].penalties, "0")

    @patch(
        'builtins.open',
        new_callable=mock_open,
        read_data='[{"user_id": "999", "user_type": "unknown", "username": "test"}]',
    )
    @patch('os.path.exists')
    def test_load_all_unknown_user_type(self, mock_exists, mock_file):
        """Test with unknown user type"""
        mock_exists.return_value = True

        with self.assertRaises(ValueError) as context:
            load_all("test_path.json")
        self.assertIn("Unknown user type", str(context.exception))

    @patch(
        'builtins.open',
        new_callable=mock_open,
        read_data='[{"user_id": "1", "user_type": "admin", "username": "a1", '
        '"email": "a@test.com", "password": "p", "passwordHash": "h", "is_locked": false,'
        ' "admin_id": "11"}, {"user_id": "2", "user_type": "customer", "username": "c1", '
        '"email": "c@test.com", "password": "p", "passwordHash": "h", "is_locked": false, '
        '"customer_id": "22", "penalties": "0", "bookmarks": []}]',
    )
    @patch('os.path.exists')
    def test_load_all_multiple_users(self, mock_exists, mock_file):
        """Test loading multiple users"""
        mock_exists.return_value = True

        users = load_all("test_path.json")

        self.assertEqual(len(users), 2)
        self.assertIsInstance(users[0], Admin)
        self.assertIsInstance(users[1], Customers)


class TestSaveAll(unittest.TestCase):
    """Unit tests for save_all function"""

    @patch('os.makedirs')
    @patch('os.path.dirname')
    @patch('builtins.open', new_callable=mock_open)
    def test_save_all_creates_directory(self, mock_file, mock_dirname, mock_makedirs):
        """Test that directory is created if it doesn't exist"""
        mock_dirname.return_value = "some/path"

        save_all([{"user_id": "123", "username": "test"}], "some/path/users.json")

        mock_makedirs.assert_called_once_with("some/path", exist_ok=True)

    @patch('os.makedirs')
    @patch('os.path.dirname')
    @patch('builtins.open', new_callable=mock_open)
    def test_save_all_with_dict(self, mock_file, mock_dirname, mock_makedirs):
        """Test saving dictionaries"""
        mock_dirname.return_value = ""
        data = [{"user_id": "123", "username": "test"}]

        save_all(data, "test.json")

        mock_file.assert_called_once_with("test.json", "w", encoding="utf-8")
        handle = mock_file()
        written_data = ''.join(call.args[0] for call in handle.write.call_args_list)
        self.assertIn("test", written_data)

    @patch('os.makedirs')
    @patch('os.path.dirname')
    @patch('builtins.open', new_callable=mock_open)
    def test_save_all_with_pydantic_model(self, mock_file, mock_dirname, mock_makedirs):
        """Test saving Pydantic models"""
        mock_dirname.return_value = ""
        admin = Admin(
            user_id="123",
            user_type="admin",
            username="admin1",
            email="admin@test.com",
            password="pass",
            passwordHash="hash",
            admin_id="456",
        )

        save_all([admin], "test.json")

        mock_file.assert_called_once()
        handle = mock_file()
        written_data = ''.join(call.args[0] for call in handle.write.call_args_list)
        self.assertIn("admin1", written_data)


class TestUserRepository(unittest.TestCase):
    """Unit tests for UserRepository class"""

    @patch('backend.repositories.users_repo.load_all')
    def setUp(self, mock_load):
        """Setup for each test"""
        mock_load.return_value = []
        self.repo = UserRepository("fake_path.json")

    def test_new_user_id_generates_unique_ids(self):
        """Test that unique IDs are generated"""
        id1 = self.repo.new_user_id()
        id2 = self.repo.new_user_id()

        self.assertNotEqual(id1, id2)
        self.assertEqual(len(id1), 32)  # UUID hex length

    def test_user_exists(self):
        """Test user existence verification"""
        admin = Admin(
            user_id="123",
            user_type="admin",
            username="admin1",
            email="admin@test.com",
            password="pass",
            passwordHash="hash",
            admin_id="456",
        )
        self.repo.users.append(admin)

        self.assertTrue(self.repo.user_exists("123"))
        self.assertFalse(self.repo.user_exists("non_existent_id"))

    def test_username_exists(self):
        """Test username existence verification"""
        admin = Admin(
            user_id="123",
            user_type="admin",
            username="testuser",
            email="test@test.com",
            password="pass",
            passwordHash="hash",
            admin_id="456",
        )
        self.repo.users.append(admin)

        self.assertTrue(self.repo.username_exists("testuser"))
        self.assertFalse(self.repo.username_exists("nonexistent"))

    def test_get_user_by_username(self):
        """Test getting user by username"""
        admin = Admin(
            user_id="123",
            user_type="admin",
            username="testuser",
            email="test@test.com",
            password="pass",
            passwordHash="hash",
            admin_id="456",
        )
        self.repo.users.append(admin)

        found = self.repo.get_user_by_username("testuser")
        self.assertIsNotNone(found)
        self.assertEqual(found.user_id, "123")

        not_found = self.repo.get_user_by_username("nonexistent")
        self.assertIsNone(not_found)

    @patch('backend.repositories.users_repo.save_all')
    def test_save_method(self, mock_save_all):
        """Test repository save method"""
        admin = Admin(
            user_id="123",
            user_type="admin",
            username="admin1",
            email="admin@test.com",
            password="pass",
            passwordHash="hash",
            admin_id="456",
        )
        self.repo.users.append(admin)

        self.repo.save()

        mock_save_all.assert_called_once_with(self.repo.users, path=self.repo.file_path)

    def test_file_path_stored(self):
        """Test that file path is stored in repository"""
        self.assertEqual(self.repo.file_path, "fake_path.json")


if __name__ == '__main__':
    unittest.main()
