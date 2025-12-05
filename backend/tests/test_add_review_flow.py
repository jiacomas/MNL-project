import os
import shutil

import pytest

from backend.repositories.reviews_repo import _movie_csv_path
from backend.schemas.reviews import ReviewCreate
from backend.services import reviews_service

# Setup a test movie directory
TEST_MOVIE = "Test Movie 123"
TEST_USER_ID = "user_test_123"
TEST_USERNAME = "TestUser"


@pytest.fixture
def clean_test_data():
    # Cleanup before and after
    path = _movie_csv_path(TEST_MOVIE)
    if os.path.exists(os.path.dirname(path)):
        shutil.rmtree(os.path.dirname(path))
    yield
    if os.path.exists(os.path.dirname(path)):
        shutil.rmtree(os.path.dirname(path))


def test_add_and_get_review(clean_test_data):
    # 1. Create a review
    payload = ReviewCreate(
        movie_name=TEST_MOVIE,
        rating=8,
        title_review="Great Movie",
        comment="I really enjoyed this test movie.",
    )

    # Mock user repository to return a user object
    from unittest.mock import MagicMock, patch

    with patch("backend.services.reviews_service.UserRepository") as MockUserRepo:
        mock_repo = MockUserRepo.return_value
        mock_user = MagicMock()
        mock_user.username = TEST_USERNAME
        mock_repo.get_by_id.return_value = mock_user

        created_review = reviews_service.create_review(payload, TEST_USER_ID)

    assert created_review.movie_name == TEST_MOVIE
    assert created_review.user_id == TEST_USER_ID
    assert created_review.username == TEST_USERNAME
    assert created_review.rating == 8
    assert created_review.title_review == "Great Movie"
    assert created_review.comment == "I really enjoyed this test movie."
    assert created_review.review_id is not None

    # 2. Retrieve the review
    retrieved_review = reviews_service.get_review_by_user(TEST_MOVIE, TEST_USER_ID)

    assert retrieved_review is not None
    assert retrieved_review.review_id == created_review.review_id
    assert retrieved_review.comment == "I really enjoyed this test movie."

    print("\nSuccessfully added and retrieved review!")
