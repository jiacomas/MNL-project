from unittest.mock import Mock, patch

from backend.schemas.movies import MovieOut
from backend.services.analytics_service import AnalyticsService


def test_search_reviews_by_title_uses_title_not_id():
    """
    Test that search_reviews_by_title calls review_repo.list_by_movie
    with the movie title, not the movie ID.
    """
    # Mock repositories
    mock_analytics_repo = Mock()
    mock_review_repo = Mock()

    # Mock MovieRepository
    with patch("backend.repositories.movies_repo.MovieRepository") as MockMovieRepo:
        mock_movie_repo_instance = MockMovieRepo.return_value

        # Setup mock movie
        mock_movie = Mock(spec=MovieOut)
        mock_movie.movie_id = "uuid-1234"
        mock_movie.title = "Test Movie Title"

        # Setup search return
        mock_movie_repo_instance.search.return_value = ([mock_movie], 1)

        # Setup review repo return
        mock_review_repo.list_by_movie.return_value = ([], None)

        # Initialize service
        service = AnalyticsService(
            analytics_repo=mock_analytics_repo, review_repo=mock_review_repo
        )

        # Execute search
        service.search_reviews_by_title("Test")

        # Verify list_by_movie was called with title, NOT ID
        # This assertion is expected to FAIL before the fix
        mock_review_repo.list_by_movie.assert_called_with(
            "Test Movie Title", limit=10000
        )
