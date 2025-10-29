import os
import csv
import json
from collections import defaultdict

def load_all_metadata(base_dir: str = "backend/data"):
    """Load all JSON metadata files from nested directories."""
    data = {}

    for root, _, files in os.walk(base_dir):
        for file in files:
            if file.endswith(".json"):
                file_path = os.path.join(root, file)
                with open(file_path, "r", encoding="utf-8") as f:
                    try:
                        content = json.load(f)
                    except json.JSONDecodeError:
                        content = None
                data[root.split("/")[-1]] = content

    return data

def load_all_reviews(base_dir: str = "backend/data"):
    """Load all review CSV files and organize them by movie."""
    reviews_by_movie = defaultdict(list)

    for root, _, files in os.walk(base_dir):
        for file in files:
            if file.endswith(".csv"):
                file_path = os.path.join(root, file)

                with open(file_path, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        review_data = {
                            "date": row.get("Date of Review"),
                            "user": row.get("User") or "Unknown",
                            "usefulness_vote": row.get("Usefulness Vote"),
                            "total_votes": row.get("Total Votes"),
                            "rating": row.get("User's Rating out of 10"),
                            "title": row.get("Review Title"),
                            "review": row.get("Review"),
                        }

                        reviews_by_movie[root.split("/")[-1]].append(review_data)

    return dict(reviews_by_movie)


if __name__ == "__main__":
    metadata = load_all_metadata()
    reviews = load_all_reviews()

    print("loaded metadata for", len(metadata), "items")
    print("loaded reviews for", sum(len(revs) for revs in reviews.values()), "reviews")