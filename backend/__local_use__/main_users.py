import json

from backend.__local_use__.create_users import main as create_users
from backend.repositories.users_repo import UserRepository, save_all


def main():
    create_users()
    repository = UserRepository()
    users = repository.users

    while True:
        print(
            "\n\n***** MENU *****\n 1. List Users\n 2. Add User\n 3. Remove User\n 4. Exit"
        )
        choice = input("Enter your choice: ")
        if choice == "1":
            print(f"Loaded {len(users)} users.")
            for user in users:
                if hasattr(user, "__dict__"):
                    obj = user.__dict__
                else:
                    obj = str(user)
                print(json.dumps(obj, ensure_ascii=False, indent=2))
        elif choice == "2":
            username = input("Enter username: ")
            password = input("Enter password: ")
            email = input("Enter email: ")
            print("Choose type of user to add:\n 1. Admin\n 2. Customer")
            user_type = input("Enter your choice: ")
            if user_type == "1":
                new_user = repository.create_user(
                    username=username, email=email, password=password, user_type="admin"
                )
            else:
                penalties = input("Enter penalties (default ''): ") or ""
                bookmarks_input = input(
                    "Enter bookmarks separated by commas (default none): "
                )
                new_user = repository.create_user(
                    username=username,
                    email=email,
                    password=password,
                    user_type="customer",
                    penalties=penalties,
                    bookmarks=bookmarks_input.split(",") if bookmarks_input else [],
                )
            users.append(new_user)
            save_all(users)
            print("User added successfully.")
        elif choice == "3":
            print("users:", [user.username for user in users])
            username = input("Enter username to remove: ")
            if not repository.username_exists(username):
                print("User not found.")
                return
            users = [user for user in users if user.username != username]
            save_all(users)
            print("User removed successfully.")
        elif choice == "4":
            print("Exiting...")
            break


if __name__ == "__main__":
    main()
