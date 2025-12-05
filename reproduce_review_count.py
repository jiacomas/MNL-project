import os
import shutil
import sys
import uuid
from datetime import datetime

from backend.repositories.reviews_repo import CSVReviewRepo
from backend.schemas.reviews import ReviewOut
from backend.services.reviews_service import get_all_reviews_for_user

# Add project root to path
sys.path.append(os.getcwd())

# Setup a temporary test directory for movie data
TEST_DATA_DIR = "temp_test_movie_data"
os.environ["MOVIE_DATA_PATH"] = TEST_DATA_DIR

if os.path.exists(TEST_DATA_DIR):
    shutil.rmtree(TEST_DATA_DIR)
os.makedirs(TEST_DATA_DIR)


def test_review_counting():
    repo = CSVReviewRepo()

    user_id = str(uuid.uuid4())
    username = "testuser"
    movie_name = "TestMovie"

    # Create a review directly via repo to simulate existing data
    review = ReviewOut(
        review_id=str(uuid.uuid4()),
        movie_name=movie_name,
        username=username,
        user_id=user_id,
        rating=8,
        title_review="Great!",
        comment="Loved it",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        usefulness=0,
        total_votes=0,
    )

    repo.create(review)

    # Now try to fetch it via service
    reviews = get_all_reviews_for_user(user_id)

    print(f"User ID: {user_id}")
    print(f"Reviews found: {len(reviews)}")

    if len(reviews) == 1:
        print("SUCCESS: Review count is correct.")
    else:
        print("FAILURE: Review count is incorrect.")

    # Clean up
    if os.path.exists(TEST_DATA_DIR):
        shutil.rmtree(TEST_DATA_DIR)


if __name__ == "__main__":
    test_review_counting()
