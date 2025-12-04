"""
Integration tests for movie service with API metadata fetching.
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from backend.schemas.movies import MovieCreate
from backend.services.movie_metadata_client import MovieMetadata
from backend.services.movies_service import create_movie


class TestMovieServiceWithAPIMetadata:
    """Test movie service integration with external API metadata fetching."""

    @patch("backend.services.movie_metadata_client.fetch_movie_metadata")
    @patch("backend.settings.ENABLE_METADATA_FETCH", True)
    def test_create_movie_with_api_metadata(self, mock_fetch):
        """Test creating a movie with only title, metadata fetched from API."""
        # Mock the API response
        mock_metadata = MovieMetadata(
            title="The Matrix",
            description="A computer hacker learns about the true nature of reality.",
            year=1999,
            genres="Action, Science Fiction",
            duration=136,
            directors="Lana Wachowski, Lilly Wachowski",
            creators="Lana Wachowski, Lilly Wachowski",
            main_stars="Keanu Reeves, Laurence Fishburne, Carrie-Anne Moss",
        )
        mock_fetch.return_value = mock_metadata

        # Mock repository
        mock_repo = MagicMock()
        mock_repo.create.return_value = MagicMock(
            movie_id="test-id",
            title="The Matrix",
            description=mock_metadata.description,
            duration=mock_metadata.duration,
        )

        # Create movie with minimal data
        movie_create = MovieCreate(title="The Matrix", year=1999)

        create_movie(movie_create, is_admin=True, repo=mock_repo)

        # Verify API was called
        mock_fetch.assert_called_once_with(title="The Matrix", year=1999)

        # Verify movie was created with enriched data
        assert mock_repo.create.called
        created_movie = mock_repo.create.call_args[0][0]
        assert created_movie.title == "The Matrix"
        assert created_movie.description == mock_metadata.description
        assert created_movie.duration == mock_metadata.duration
        assert created_movie.movieGenres == mock_metadata.genres
        assert created_movie.directors == mock_metadata.directors

    @patch("backend.services.movie_metadata_client.fetch_movie_metadata")
    @patch("backend.settings.ENABLE_METADATA_FETCH", True)
    def test_create_movie_manual_override(self, mock_fetch):
        """Test that user-provided data takes precedence over API data."""
        mock_metadata = MovieMetadata(
            title="The Matrix",
            description="API description",
            duration=136,
            genres="Action",
        )
        mock_fetch.return_value = mock_metadata

        mock_repo = MagicMock()
        mock_repo.create.return_value = MagicMock()

        # User provides their own description
        movie_create = MovieCreate(
            title="The Matrix",
            description="User's custom description",
            duration=140,  # User override
        )

        create_movie(movie_create, is_admin=True, repo=mock_repo)

        # Verify user data was preserved
        created_movie = mock_repo.create.call_args[0][0]
        assert created_movie.description == "User's custom description"
        assert created_movie.duration == 140

    @patch("backend.services.movie_metadata_client.fetch_movie_metadata")
    @patch("backend.settings.ENABLE_METADATA_FETCH", True)
    def test_create_movie_api_failure(self, mock_fetch):
        """Test that movie creation fails gracefully when API fails."""
        # API returns None (movie not found or error)
        mock_fetch.return_value = None

        mock_repo = MagicMock()

        # Try to create movie with only title
        movie_create = MovieCreate(title="Unknown Movie")

        # Should raise error because required fields are missing
        with pytest.raises(HTTPException) as exc:
            create_movie(movie_create, is_admin=True, repo=mock_repo)

        assert exc.value.status_code == 400
        assert "description is required" in str(exc.value.detail)

    @patch("backend.services.movie_metadata_client.fetch_movie_metadata")
    @patch("backend.settings.ENABLE_METADATA_FETCH", True)
    def test_create_movie_api_exception(self, mock_fetch):
        """Test handling when API raises an exception."""
        # API raises exception
        mock_fetch.side_effect = Exception("Network error")

        mock_repo = MagicMock()

        # Try to create movie with only title
        movie_create = MovieCreate(title="Test Movie")

        # Should raise error because required fields are missing after API failure
        with pytest.raises(HTTPException) as exc:
            create_movie(movie_create, is_admin=True, repo=mock_repo)

        assert exc.value.status_code == 400

    @patch("backend.services.movie_metadata_client.fetch_movie_metadata")
    @patch("backend.settings.ENABLE_METADATA_FETCH", False)
    def test_create_movie_api_disabled(self, mock_fetch):
        """Test that API is not called when feature is disabled."""
        mock_repo = MagicMock()

        # Try to create movie with only title
        movie_create = MovieCreate(title="Test Movie")

        # Should fail because API is disabled and fields are missing
        with pytest.raises(HTTPException) as exc:
            create_movie(movie_create, is_admin=True, repo=mock_repo)

        # API should not have been called
        mock_fetch.assert_not_called()
        assert exc.value.status_code == 400

    @patch("backend.services.movie_metadata_client.fetch_movie_metadata")
    @patch("backend.settings.ENABLE_METADATA_FETCH", True)
    def test_create_movie_partial_metadata(self, mock_fetch):
        """Test creating movie when API returns partial metadata."""
        # API returns partial data
        mock_metadata = MovieMetadata(
            title="Partial Movie",
            description="A description",
            duration=90,
            # Missing genres, directors, etc.
        )
        mock_fetch.return_value = mock_metadata

        mock_repo = MagicMock()
        mock_repo.create.return_value = MagicMock()

        # User provides title, API fills in description and duration
        movie_create = MovieCreate(title="Partial Movie")

        create_movie(movie_create, is_admin=True, repo=mock_repo)

        # Verify partial enrichment
        created_movie = mock_repo.create.call_args[0][0]
        assert created_movie.description == "A description"
        assert created_movie.duration == 90
        # These should remain None since API didn't provide them
        assert created_movie.movieGenres is None
        assert created_movie.directors is None

    @patch("backend.services.movie_metadata_client.fetch_movie_metadata")
    @patch("backend.settings.ENABLE_METADATA_FETCH", True)
    def test_create_movie_with_year_improves_search(self, mock_fetch):
        """Test that providing year parameter improves API search accuracy."""
        mock_metadata = MovieMetadata(
            title="Dune",
            description="2021 version",
            year=2021,
            duration=155,
        )
        mock_fetch.return_value = mock_metadata

        mock_repo = MagicMock()
        mock_repo.create.return_value = MagicMock()

        # Create movie with year specified
        movie_create = MovieCreate(title="Dune", year=2021)

        create_movie(movie_create, is_admin=True, repo=mock_repo)

        # Verify year was passed to API
        mock_fetch.assert_called_once_with(title="Dune", year=2021)

    @patch("backend.services.movie_metadata_client.fetch_movie_metadata")
    @patch("backend.settings.ENABLE_METADATA_FETCH", True)
    def test_create_movie_all_fields_provided_skips_api(self, mock_fetch):
        """Test that API is not called when all fields are provided."""
        mock_repo = MagicMock()
        mock_repo.create.return_value = MagicMock()

        # Create movie with all fields
        movie_create = MovieCreate(
            title="Complete Movie",
            description="Full description",
            duration=120,
            movieGenres="Action",
            directors="Director Name",
            creators="Creator Name",
            mainStars="Star Name",
            datePublished="2024-01-01",
        )

        create_movie(movie_create, is_admin=True, repo=mock_repo)

        # API should not be called since all fields are present
        mock_fetch.assert_not_called()
