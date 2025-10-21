import pytest
import json

from backend.services.review_service import ReviewService
from backend.services.auth_service import AuthService
from backend.repositories.items_repo import Repository

@pytest.fixture
def test_repository(self, temp_data_dir):
    """create real repository pointing to a temp file"""
    reviews_file = temp_data_dir / "reviews.json"
    # initialize the file with an empty structure
    with open(reviews_file, 'w') as f:
        json.dump({"reviews": []}, f)
    
    repo = Repository(str(reviews_file))
    return repo

@pytest.fixture
def review_service(self, test_repository):
    """ReviewService with real repository"""
    return ReviewService(repository=test_repository)

def test_create_review_persists_to_file(self, review_service, test_repository):
    """
    ReviewService.create_review() → Repository.write() → File System
    - verify that reviews are correctly saved to the file
    """
    # execute: create a review
    result = review_service.create_review(
        user_id=1,
        movie_id=123,
        rating=5,
        comment="Amazing movie! A masterpiece of cinema."
    )

    # verifications of the result
    assert "review_id" in result
    assert result["success"] == True
    review_id = result["review_id"]

    # integration verification: read directly from the repository
    saved_review = test_repository.find_by_id(review_id)
    assert saved_review is not None
    assert saved_review["rating"] == 5
    assert saved_review["movie_id"] == 123
    assert "Amazing movie" in saved_review["comment"]

    # verification of the file system: read the file directly
    with open(test_repository.file_path, 'r') as f:
        file_data = json.load(f)
    
    assert len(file_data["reviews"]) == 1
    assert file_data["reviews"][0]["review_id"] == review_id

def test_update_review_modifies_file(self, review_service, test_repository):
    """
    Create → Update → Verify persistence
    """
    # create review
    create_result = review_service.create_review(
        user_id=1, movie_id=456, rating=3,
        comment="Initial comment here"
    )
    review_id = create_result["review_id"]
    
    # update review
    update_result = review_service.update_review(
        review_id=review_id,
        rating=5,
        comment="Updated comment - much better!"
    )
    
    assert update_result["success"] == True

    # verify that the update was persisted
    updated_review = test_repository.find_by_id(review_id)
    assert updated_review["rating"] == 5
    assert "Updated comment" in updated_review["comment"]
    assert "Initial comment" not in updated_review["comment"]

def test_delete_review_removes_from_file(self, review_service, test_repository):
    """
    Create → Delete → Verify it no longer exists
    """
    # create review
    create_result = review_service.create_review(
        user_id=1, movie_id=789, rating=4,
        comment="This review will be deleted"
    )
    review_id = create_result["review_id"]

    # verify that it exists
    assert test_repository.find_by_id(review_id) is not None
    
    # delete
    delete_result = review_service.delete_review(review_id)
    assert delete_result["success"] == True

    # verify that it no longer exists
    assert test_repository.find_by_id(review_id) is None

    # verify in the file
    with open(test_repository.file_path, 'r') as f:
        file_data = json.load(f)
    
    review_ids = [r["review_id"] for r in file_data["reviews"]]
    assert review_id not in review_ids

def test_multiple_reviews_from_different_users(self, review_service):
    """
    multiple users creating reviews simultaneously
    """
    # create reviews from different users
    review1 = review_service.create_review(
        user_id=1, movie_id=100, rating=5,
        comment="User 1 loves this movie"
    )
    
    review2 = review_service.create_review(
        user_id=2, movie_id=100, rating=2,
        comment="User 2 dislikes this movie"
    )
    
    review3 = review_service.create_review(
        user_id=3, movie_id=100, rating=4,
        comment="User 3 thinks it's good"
    )

    # get all reviews from the movie
    movie_reviews = review_service.get_reviews_by_movie(movie_id=100)
    
    assert len(movie_reviews) == 3
    ratings = [r["rating"] for r in movie_reviews]
    assert 5 in ratings
    assert 2 in ratings
    assert 4 in ratings

@pytest.fixture
def concurrent_repository(self, temp_data_dir):
    """repository with locking enabled"""
    file_path = temp_data_dir / "concurrent_test.json"
    with open(file_path, 'w') as f:
        json.dump({"data": []}, f)
    return Repository(str(file_path), use_locking=True)

def test_concurrent_writes_no_corruption(self, concurrent_repository):
    """
    multiple threads writing simultaneously
    - verify that file locking prevents data corruption
    """
    import threading
    import time
    
    def write_data(thread_id):
        for i in range(5):
            concurrent_repository.write({
                "thread_id": thread_id,
                "iteration": i,
                "timestamp": time.time()
            })

    # create 10 threads that write simultaneously
    threads = []
    for thread_id in range(10):
        t = threading.Thread(target=write_data, args=(thread_id,))
        threads.append(t)
        t.start()

    for t in threads: # wait for all threads to finish
        t.join()

    # verify data integrity
    all_data = concurrent_repository.read_all()

    # 10 threads × 5 iterations = 50 entries
    assert len(all_data["data"]) == 50

    # verify that there is no JSON corruption
    with open(concurrent_repository.file_path, 'r') as f:
        content = f.read()
        # if there is corruption, this will raise JSONDecodeError
        json.loads(content)