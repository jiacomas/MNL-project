"""
Tests for MovieListResponse schema using multiple testing methodologies.
"""
import pytest
from datetime import datetime, timezone
from backend.app.schemas.movies import MovieListResponse, MovieOut


class TestMovieListResponseSchema:
    """Comprehensive tests for MovieListResponse schema with multiple testing methodologies"""

    def test_movie_list_response_valid_data(self):
        """Test MovieListResponse with valid data"""
        now = datetime.now(timezone.utc)
        movie_data = {
            "movie_id": "tt0111161",
            "title": "Test Movie",
            "created_at": now,
            "updated_at": now,
            "review_count": 0
        }

        movie = MovieOut(**movie_data)

        response_data = {
            "items": [movie],
            "total": 100,
            "page": 1,
            "page_size": 50,
            "total_pages": 2
        }

        response = MovieListResponse(**response_data)
        assert len(response.items) == 1
        assert response.items[0].movie_id == "tt0111161"
        assert response.total == 100
        assert response.page == 1
        assert response.page_size == 50
        assert response.total_pages == 2

    def test_movie_list_response_empty_items(self):
        """Test MovieListResponse with empty items list"""
        response_data = {
            "items": [],
            "total": 0,
            "page": 1,
            "page_size": 50,
            "total_pages": 0
        }

        response = MovieListResponse(**response_data)
        assert len(response.items) == 0
        assert response.total == 0
        assert response.total_pages == 0

    def test_movie_list_response_multiple_items(self):
        """Test MovieListResponse with multiple items"""
        now = datetime.now(timezone.utc)
        movies = [
            MovieOut(
                movie_id=f"tt{i:07d}",
                title=f"Movie {i}",
                created_at=now,
                updated_at=now,
                review_count=i * 100
            )
            for i in range(1, 6)
        ]

        response_data = {
            "items": movies,
            "total": 100,
            "page": 2,
            "page_size": 5,
            "total_pages": 20
        }

        response = MovieListResponse(**response_data)
        assert len(response.items) == 5
        assert response.items[0].movie_id == "tt0000001"
        assert response.items[4].movie_id == "tt0000005"
        assert response.page == 2
        assert response.total_pages == 20

    # Boundary Value Analysis
    @pytest.mark.parametrize("page,page_size,total,total_pages", [
        (1, 1, 1, 1),  # Minimum values
        (1, 50, 100, 2),  # Normal values
        (10, 100, 1000, 10),  # Larger values
        (1, 100, 0, 0),  # Zero total
    ])
    def test_movie_list_response_pagination_boundary_values(self, page, page_size, total, total_pages):
        """Test MovieListResponse with pagination boundary values"""
        now = datetime.now(timezone.utc)
        items = [
            MovieOut(
                movie_id="tt0111161",
                title="Test Movie",
                created_at=now,
                updated_at=now,
                review_count=0
            )
        ] if total > 0 else []

        response_data = {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }

        response = MovieListResponse(**response_data)
        assert response.page == page
        assert response.page_size == page_size
        assert response.total == total
        assert response.total_pages == total_pages

    # Equivalence Partitioning Tests
    @pytest.mark.parametrize("item_count", [0, 1, 5, 10])
    def test_movie_list_response_item_count_equivalence(self, item_count):
        """Test MovieListResponse with different item counts"""
        now = datetime.now(timezone.utc)
        items = [
            MovieOut(
                movie_id=f"tt{i:07d}",
                title=f"Movie {i}",
                created_at=now,
                updated_at=now,
                review_count=i * 100
            )
            for i in range(item_count)
        ]

        response_data = {
            "items": items,
            "total": item_count * 10,  # Simulate more total items than current page
            "page": 1,
            "page_size": 10,
            "total_pages": max(1, (item_count * 10) // 10)
        }

        response = MovieListResponse(**response_data)
        assert len(response.items) == item_count
        assert response.total == item_count * 10

    # Performance and Edge Case Tests
    def test_movie_list_response_large_dataset(self):
        """Test MovieListResponse with large number of items"""
        now = datetime.now(timezone.utc)
        # Create a larger but reasonable number of items
        large_movie_list = [
            MovieOut(
                movie_id=f"tt{i:07d}",
                title=f"Movie {i}",
                created_at=now,
                updated_at=now,
                review_count=i * 100
            )
            for i in range(100)  # Larger dataset
        ]

        response = MovieListResponse(
            items=large_movie_list,
            total=10000,
            page=1,
            page_size=100,
            total_pages=100
        )

        assert len(response.items) == 100
        assert response.total == 10000
        assert response.total_pages == 100