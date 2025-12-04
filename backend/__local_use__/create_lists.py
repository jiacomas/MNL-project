import argparse
import os
import random
import sys

from backend.repositories.movies_repo import MovieRepository
from backend.repositories.users_repo import UserRepository
from backend.schemas.lists import ListCreate
from backend.services import lists_service

# Add the project root to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


def get_random_user_id():
    """Try to get a random user ID from users.json, else return a mock one."""
    try:
        repo = UserRepository()
        users = repo.users
        if users:
            return random.choice(users).user_id
    except Exception:
        pass
    return "mock-user-123"


def get_movies_by_genre(genre_keyword=None, limit=5):
    """Get random movies, optionally filtered by genre keyword."""
    try:
        repo = MovieRepository(use_json=False)  # Use CSV format
        all_movies, total = repo.get_all(skip=0, limit=1000)

        if genre_keyword:
            # Filter by genre - handle both dict and object formats
            filtered = []
            for m in all_movies:
                genres = (
                    m.movieGenres
                    if hasattr(m, 'movieGenres')
                    else m.get("movieGenres", "")
                )
                if genres and genre_keyword.lower() in genres.lower():
                    filtered.append(m)
            movies = filtered[:limit] if filtered else all_movies[:limit]
        else:
            movies = all_movies[:limit]

        # Extract movie IDs - handle both dict and object formats
        movie_ids = []
        for m in movies:
            movie_id = m.movie_id if hasattr(m, 'movie_id') else m.get("movie_id")
            if movie_id:
                movie_ids.append(movie_id)

        return movie_ids
    except Exception as e:
        print(f"Warning: Could not load movies from repository: {e}")
        return []


def create_sample_lists(user_id):
    print(f"Creating sample lists for user: {user_id}")
    print("Loading movies from movies.json...")

    # Define list templates with genre filters
    samples = [
        {
            "name": "Action Packed",
            "description": "High-octane action movies for an adrenaline rush.",
            "genre": "Action",
            "count": 5,
        },
        {
            "name": "Sci-Fi Favorites",
            "description": "The best science fiction movies of all time.",
            "genre": "Sci-Fi",
            "count": 4,
        },
        {
            "name": "Drama Collection",
            "description": "Compelling dramas that tell powerful stories.",
            "genre": "Drama",
            "count": 5,
        },
        {
            "name": "Weekend Watchlist",
            "description": "A mix of movies to watch this weekend.",
            "genre": None,  # Random selection
            "count": 6,
        },
    ]

    for sample in samples:
        try:
            # Get movies for this list
            movie_ids = get_movies_by_genre(sample["genre"], sample["count"])

            if not movie_ids:
                print(f"Skipping list '{sample['name']}' - no movies found")
                continue

            # Create List
            list_in = ListCreate(name=sample["name"], description=sample["description"])
            new_list = lists_service.create_list(list_in, user_id)
            print(f"Created list '{new_list.name}' (ID: {new_list.id})")

            # Add Movies
            for movie_id in movie_ids:
                lists_service.add_movie_to_list(str(new_list.id), movie_id, user_id)
                print(f"  - Added movie {movie_id}")

        except Exception as e:
            print(f"Error creating list '{sample['name']}': {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Create example lists for users using data from movies.json and users.json."
    )
    parser.add_argument(
        "--user-id",
        help="User ID to assign lists to. If not provided, picks a random user.",
    )
    parser.add_argument("--name", help="Name of a single list to create.")
    parser.add_argument("--description", help="Description of the single list.")
    parser.add_argument(
        "--genre", help="Genre filter for movies (only used with --name)."
    )
    parser.add_argument(
        "--count",
        type=int,
        default=5,
        help="Number of movies to add to the list (default: 5).",
    )

    args = parser.parse_args()

    user_id = args.user_id or get_random_user_id()

    if args.name:
        # Create single specific list
        print(f"Creating single list '{args.name}' for user {user_id}")
        try:
            movie_ids = get_movies_by_genre(args.genre, args.count)

            if not movie_ids:
                print("No movies found matching criteria")
                return

            list_in = ListCreate(name=args.name, description=args.description)
            new_list = lists_service.create_list(list_in, user_id)
            print(f"Successfully created list: {new_list.id}")

            # Add movies
            for movie_id in movie_ids:
                lists_service.add_movie_to_list(str(new_list.id), movie_id, user_id)
                print(f"  - Added movie {movie_id}")
        except Exception as e:
            print(f"Failed to create list: {e}")
    else:
        # Create sample set
        create_sample_lists(user_id)


if __name__ == "__main__":
    main()
