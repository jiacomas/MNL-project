import csv
import json
import os
import uuid

MOVIE_METADATA = "metadata.json"
MOVIE_REVIEWS = "movieReviews.csv"


def make_movie_id(movie_id, entry):
    if movie_id is not None:
        return movie_id
    return uuid.uuid5(uuid.NAMESPACE_DNS, entry)


def get_movie_metadata(movie_path, entry):  # noqa: C901
    metadata_path = os.path.join(movie_path, MOVIE_METADATA)

    metadata_content = {}

    # Load metadata.json
    try:
        with open(metadata_path, "r", encoding="utf-8") as f:
            try:
                metadata_content = json.load(f)
                # Ensure the metadata contains a `movie_id` string field
                try:
                    raw_id = metadata_content.get("movie_id", None)
                    if raw_id is None:
                        raise ValueError
                    # accept ints or numeric strings -> coerce to string
                    metadata_content["movie_id"] = str(raw_id)
                except (ValueError, TypeError):
                    metadata_content["movie_id"] = make_movie_id(None, entry)

                # write the updated metadata back to the JSON file
                try:
                    # close the read handle before opening for write (safe even if closed twice)
                    try:
                        f.close()
                    except Exception:
                        pass
                    with open(metadata_path, "w", encoding="utf-8") as wf:
                        json.dump(metadata_content, wf, ensure_ascii=False, indent=2)
                except (OSError, TypeError):
                    # ignore write errors and keep metadata in-memory
                    pass
            except json.JSONDecodeError:
                metadata_content = {}
    except (FileNotFoundError, OSError):
        metadata_content = {}

    return metadata_content


def get_movie_reviews(movie_path, movie_id, entry):
    reviews_path = os.path.join(movie_path, MOVIE_REVIEWS)

    reviews_content = ""

    # Load movieReviews.csv
    try:
        with open(reviews_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            reviews_content = []
            for row in reader:
                # add the film id to each review row
                row["movie_title"] = entry
                row["movie_id"] = movie_id
                reviews_content.append(row)
    except (FileNotFoundError, OSError):
        reviews_content = []
    except Exception:
        # fallback: return empty list on unexpected parse errors
        reviews_content = []

    return reviews_content


def explore_each_movie(original_path="backend/data/movies"):  # noqa: C901
    root = os.path.abspath(original_path)
    if not os.path.isdir(root):
        return []

    for entry in sorted(os.listdir(root)):
        movie_path = os.path.join(root, entry)
        if not os.path.isdir(movie_path):
            continue

        metadata_content = get_movie_metadata(movie_path, entry)
        # Ensure movie_id is a string (consistent with MovieBase.movie_id)
        movie_id = make_movie_id(metadata_content.get("movie_id"), entry)
        reviews_content = get_movie_reviews(movie_path, movie_id, entry)

        # Ensure metadata is a dict and add review_count for this movie
        if not isinstance(metadata_content, dict):
            metadata_content = {}
        reviews_len = len(reviews_content) if isinstance(reviews_content, list) else 0
        metadata_content["review_count"] = reviews_len

        # persist metadata and reviews into JSON files under the data root
        movies_json_path = os.path.join(root, "movies.json")
        # reviews_json_path = os.path.join(root, "reviews.json") # no needed

        # load existing movies.json (must be a list)
        try:
            with open(movies_json_path, "r", encoding="utf-8") as mf:
                existing_movies = json.load(mf)
                if not isinstance(existing_movies, list):
                    existing_movies = []
        except (FileNotFoundError, OSError, json.JSONDecodeError):
            existing_movies = []

        # load existing reviews.json (must be a list)
        # try:
        #     with open(reviews_json_path, "r", encoding="utf-8") as rf:
        #         existing_reviews = json.load(rf)
        #         if not isinstance(existing_reviews, list):
        #             existing_reviews = []
        # except (FileNotFoundError, OSError, json.JSONDecodeError):
        #     existing_reviews = []

        # append current movie metadata (include numeric movie_id and title)
        existing_movies.append(metadata_content)

        # append reviews (reviews_content is expected to be a list)
        # if isinstance(reviews_content, list):
        #     existing_reviews.extend(reviews_content)

        # write back both files (ignore write errors)
        try:
            with open(movies_json_path, "w", encoding="utf-8") as mf:
                json.dump(existing_movies, mf, ensure_ascii=False, indent=2)
        except (OSError, TypeError):
            pass

        # try:
        #     with open(reviews_json_path, "w", encoding="utf-8") as rf:
        #         json.dump(existing_reviews, rf, ensure_ascii=False, indent=2)
        # except (OSError, TypeError):
        #     pass

        yield entry, len(reviews_content)


if __name__ == "__main__":
    movies = []
    reviews = []
    for movie in explore_each_movie():
        print(movie)
