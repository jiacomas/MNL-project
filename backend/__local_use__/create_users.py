import argparse

from pydantic import ValidationError

from backend.repositories.users_repo import UserRepository, save_all
from backend.services.users_service import UsersService


# Simple CLI
def main():
    parser = argparse.ArgumentParser(
        description="Create users (Admin or Customer) and save to JSON."
    )
    parser.add_argument(
        "type",
        nargs="?",
        choices=["admin", "customer", "sample"],
        default="sample",
        help="Type of user to create (default: sample)",
    )
    parser.add_argument("--username", help="Username")
    parser.add_argument("--email", help="Email")
    parser.add_argument("--password", help="Password")
    parser.add_argument(
        "--output", default="backend/data/users.json", help="Output JSON file"
    )
    parser.add_argument("--penalties", default="", help="Penalties (customer only)")
    parser.add_argument("--bookmarks", nargs="*", help="Bookmarks (customer only)")
    args = parser.parse_args()

    repository = UserRepository()
    users = repository.users
    service = UsersService(repository)
    try:
        if args.type == "admin":
            if not (args.username and args.email and args.password):
                parser.error("admin requires --username --email --password")
            admin = service.create_user(
                args.username, args.email, args.password, user_type="admin"
            )
            users.append(admin)
            print(f"Created admin {admin.username} ({admin.user_id})")
        elif args.type == "customer":
            if not (args.username and args.email and args.password):
                parser.error("customer requires --username --email --password")
            customer = service.create_user(
                args.username,
                args.email,
                args.password,
                user_type="customer",
                penalties=args.penalties,
                bookmarks=args.bookmarks or [],
            )
            users.append(customer)
            print(f"Created customer {customer.username} ({customer.user_id})")
        elif args.type == "sample":
            # create a small sample set
            users = [
                service.create_user(
                    "admin1", "admin1@example.com", "secret1", user_type="admin"
                ),
                service.create_user(
                    "cust1",
                    "cust1@example.com",
                    "secret2",
                    user_type="customer",
                    penalties="0",
                    bookmarks=["item1", "item2"],
                ),
                service.create_user(
                    "cust2",
                    "cust2@example.com",
                    "secret3",
                    user_type="customer",
                    penalties="1",
                    bookmarks=["item3"],
                ),
            ]
            print("Created sample users")
    except ValidationError as e:
        print("Validation error:", e)
        return

    save_all(users, args.output)
    print(f"Saved {len(users)} users to {args.output}")


if __name__ == "__main__":
    main()
