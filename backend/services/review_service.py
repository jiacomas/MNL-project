from schemas.review import Review
from repositories.review_repo import ReviewRepository

class ReviewService:
    def __init__(self, repository: ReviewRepository):
        self.repository = repository

    def create_review(self, review: Review):
        self.repository.create_review(review)