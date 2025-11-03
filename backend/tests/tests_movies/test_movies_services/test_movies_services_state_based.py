"""
State-based testing for Movies Service - Testing state transitions and lifecycle
"""
import pytest
from unittest.mock import patch, create_autospec

from backend.app.services.movies_service import (
    create_movie,
    get_movie,
    update_movie,
    delete_movie,
    get_movie_stats
)
from backend.app.schemas.movies import MovieCreate, MovieUpdate, MovieOut
from backend.app.repositories.movies_repo import MovieRepository


class TestMoviesServiceStateBased:
    """State-based testing for movie lifecycle and state transitions"""

    @pytest.fixture
    def mock_repo(self):
        return create_autospec(MovieRepository)

    @pytest.fixture
    def sample_movie_out(self):
        return MovieOut(
            movie_id="tt0111161",
            title="The Shawshank Redemption",
            genre="Drama",
            release_year=1994,
            rating=9.3,
            runtime=142,
            director="Frank Darabont",
            cast="Tim Robbins, Morgan Freeman",
            plot="Two imprisoned men bond over a number of years...",
            poster_url="https://example.com/poster.jpg",
            created_at="2024-01-01T12:00:00Z",
            updated_at="2024-01-01T12:00:00Z",
            review_count=2500000
        )

    def test_movie_lifecycle_state_changes(self, mock_repo, sample_movie_out):
        """Test complete movie lifecycle state changes"""
        movie_create = MovieCreate(
            title="Lifecycle Test Movie",
            genre="Drama",
            release_year=2024
        )

        movie_update = MovieUpdate(rating=8.5)
        updated_movie = sample_movie_out.model_copy(update={"rating": 8.5})

        # Set up mock responses for each state change
        mock_repo.create.return_value = sample_movie_out
        mock_repo.get_by_id.return_value = sample_movie_out
        mock_repo.update.return_value = updated_movie
        mock_repo.delete.return_value = True

        with patch('backend.app.services.movies_service.movie_repo', mock_repo):
            # Create movie
            created_movie = create_movie(movie_create, is_admin=True)
            assert created_movie.rating == 9.3

            # Read movie
            retrieved_movie = get_movie("tt0111161")
            assert retrieved_movie.title == "The Shawshank Redemption"

            # Update movie
            updated_result = update_movie("tt0111161", movie_update, is_admin=True)
            assert updated_result.rating == 8.5

            # Delete movie
            delete_movie("tt0111161", is_admin=True)

        # Verify all state transitions were called
        mock_repo.create.assert_called_once()
        mock_repo.get_by_id.assert_called_once_with("tt0111161")
        mock_repo.update.assert_called_once_with("tt0111161", movie_update)
        mock_repo.delete.assert_called_once_with("tt0111161")

    def test_get_movie_stats_success(self, mock_repo, sample_movie_out):
        """Test getting movie statistics with state verification"""
        # Create multiple movies for stats testing
        movies_data = [
            sample_movie_out,
            MovieOut(**{**sample_movie_out.dict(), "movie_id": "tt0068646", "genre": "Crime,Drama", "rating": 9.2}),
            MovieOut(
                **{**sample_movie_out.dict(), "movie_id": "tt0468569", "genre": "Action,Crime,Drama", "rating": 9.0}),
        ]

        mock_repo.get_all.return_value = (movies_data, 3)

        with patch('backend.app.services.movies_service.movie_repo', mock_repo):
            stats = get_movie_stats()

        assert stats["total_movies"] == 3
        assert "average_rating" in stats
        assert "top_genres" in stats
        assert "year_range" in stats

        # Verify state calculations
        assert stats["average_rating"] == round((9.3 + 9.2 + 9.0) / 3, 2)
        assert any(genre[0] == "Drama" for genre in stats["top_genres"])