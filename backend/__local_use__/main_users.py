import json

from backend.__local_use__.create_users import main as create_users
from backend.repositories.users_repo import UserRepository, save_all


def print_menu():
    print(
        "\n\n***** MENU *****"
        "\n 1. List Users"
        "\n 2. Add User"
        "\n 3. Remove User"
        "\n 4. Edit User Info"
        "\n 5. Exit"
    )


def list_users(users):
    print(f"Loaded {len(users)} users.")
    for user in users:
        if hasattr(user, "__dict__"):
            obj = user.__dict__
        else:
            obj = str(user)
        print(json.dumps(obj, ensure_ascii=False, indent=2))


def add_user(repository, users):
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
        bookmarks_input = input("Enter bookmarks separated by commas (default none): ")
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


def remove_user(repository, users):
    print("users:", [user.username for user in users])
    username = input("Enter username to remove: ")
    if not repository.username_exists(username):
        print("User not found.")
        return
    # mutate the list in place so external references stay valid
    users[:] = [user for user in users if user.username != username]
    save_all(users)
    print("User removed successfully.")


def _print_users_list(users):
    print("users:", [user.username for user in users])


def _edit_email(user):
    new_email = input(f"Enter new email (current: {user.email}): ") or user.email
    user.email = new_email
    print("Email updated.")


def _edit_password(user, repository):
    new_password = input("Enter new password (leave blank to keep current): ")
    if new_password:
        # repository.hash_password may exist; fall back if it doesn't
        try:
            user.passwordHash = repository.hash_password(new_password)
        except Exception:
            user.passwordHash = new_password
        user.password = new_password
        print("Password updated.")
    else:
        print("Password unchanged.")


def _edit_user_type(user):
    new_user_type = (
        input(f"Enter new user type (current: {user.user_type}): ") or user.user_type
    )
    user.user_type = new_user_type
    print("User type updated.")


def _edit_username(user, users, repository):
    new_username = (
        input(f"Enter new username (current: {user.username}): ") or user.username
    )
    if new_username != user.username and repository.username_exists(new_username):
        print("Username already exists.")
        return
    user.username = new_username
    print("Username updated.")


def edit_user(repository, users):  # TODO: make possible to edit user_type
    _print_users_list(users)
    username = input("Enter username to edit: ")
    user = repository.get_user_by_username(username)
    if not user:
        print("User not found.")
        return

    handlers = {
        "1": lambda: _edit_email(user),
        "2": lambda: _edit_password(user, repository),
        "3": lambda: _edit_user_type(user),
        "4": lambda: _edit_username(user, users, repository),
    }

    while True:
        print(
            f"\nEditing user: {user.username}"
            "\n 1. Email"
            "\n 2. Password"
            "\n 3. User Type"
            "\n 4. Username"
            "\n 5. Done"
        )
        choice = input("Enter the number of the field you want to edit: ")
        if choice == "5":
            break

        handler = handlers.get(choice)
        if handler:
            handler()
            save_all(users)
            print("User info updated successfully.")
        else:
            print("Invalid choice, please try again.")


def main():
    create_users()
    repository = UserRepository()
    users = repository.users

    while True:
        print_menu()
        choice = input("Enter your choice: ")
        if choice == "1":
            list_users(users)
        elif choice == "2":
            add_user(repository, users)
        elif choice == "3":
            remove_user(repository, users)
        elif choice == "4":
            edit_user(repository, users)
        elif choice == "5":
            print("Exiting...")
            break
        else:
            print("Invalid choice, please try again.")


if __name__ == "__main__":
    main()
