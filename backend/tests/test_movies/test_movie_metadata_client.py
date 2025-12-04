"""
Unit tests for movie metadata client.
"""

from unittest.mock import MagicMock, patch

from backend.services.movie_metadata_client import (
    MovieMetadata,
    MovieMetadataClient,
    fetch_movie_metadata,
)


class TestMovieMetadata:
    """Test MovieMetadata data class."""

    def test_to_dict_excludes_none(self):
        """Test that to_dict excludes None values."""
        metadata = MovieMetadata(
            title="Test Movie",
            description="A test movie",
            year=2020,
            genres=None,
            duration=None,
        )
        result = metadata.to_dict()
        assert result == {
            "title": "Test Movie",
            "description": "A test movie",
            "year": 2020,
        }
        assert "genres" not in result
        assert "duration" not in result


class TestMovieMetadataClient:
    """Test MovieMetadataClient."""

    @patch("backend.services.movie_metadata_client.ENABLE_METADATA_FETCH", False)
    def test_fetch_disabled(self):
        """Test that fetching is skipped when disabled."""
        client = MovieMetadataClient()
        result = client.fetch_movie_metadata("The Matrix")
        assert result is None

    @patch("backend.services.movie_metadata_client.ENABLE_METADATA_FETCH", True)
    @patch("backend.services.movie_metadata_client.httpx.Client")
    def test_fetch_from_tmdb_success(self, mock_client_class):
        """Test successful metadata fetch from TMDB."""
        # Mock HTTP responses
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # Mock search response
        search_response = MagicMock()
        search_response.json.return_value = {
            "results": [
                {
                    "id": 603,
                    "title": "The Matrix",
                    "release_date": "1999-03-31",
                }
            ]
        }

        # Mock details response
        details_response = MagicMock()
        details_response.json.return_value = {
            "id": 603,
            "title": "The Matrix",
            "overview": "A computer hacker learns about the true nature of reality.",
            "release_date": "1999-03-31",
            "runtime": 136,
            "genres": [
                {"id": 28, "name": "Action"},
                {"id": 878, "name": "Science Fiction"},
            ],
            "credits": {
                "cast": [
                    {"name": "Keanu Reeves"},
                    {"name": "Laurence Fishburne"},
                    {"name": "Carrie-Anne Moss"},
                ],
                "crew": [
                    {"name": "Lana Wachowski", "job": "Director"},
                    {"name": "Lilly Wachowski", "job": "Director"},
                    {"name": "Lana Wachowski", "job": "Writer"},
                ],
            },
        }

        mock_client.get.side_effect = [search_response, details_response]

        client = MovieMetadataClient(
            provider="tmdb", tmdb_api_key="test_key", omdb_api_key=""
        )
        result = client.fetch_movie_metadata("The Matrix", year=1999)

        assert result is not None
        assert result.title == "The Matrix"
        assert (
            result.description
            == "A computer hacker learns about the true nature of reality."
        )
        assert result.year == 1999
        assert result.duration == 136
        assert "Action" in result.genres
        assert "Science Fiction" in result.genres
        assert "Lana Wachowski" in result.directors
        assert "Keanu Reeves" in result.main_stars

    @patch("backend.services.movie_metadata_client.ENABLE_METADATA_FETCH", True)
    @patch("backend.services.movie_metadata_client.httpx.Client")
    def test_fetch_from_tmdb_not_found(self, mock_client_class):
        """Test handling when movie is not found in TMDB."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        search_response = MagicMock()
        search_response.json.return_value = {"results": []}

        mock_client.get.return_value = search_response

        client = MovieMetadataClient(
            provider="tmdb", tmdb_api_key="test_key", omdb_api_key=""
        )
        result = client.fetch_movie_metadata("Nonexistent Movie 12345")

        assert result is None

    @patch("backend.services.movie_metadata_client.ENABLE_METADATA_FETCH", True)
    @patch("backend.services.movie_metadata_client.httpx.Client")
    def test_fetch_from_omdb_success(self, mock_client_class):
        """Test successful metadata fetch from OMDB."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        omdb_response = MagicMock()
        omdb_response.json.return_value = {
            "Response": "True",
            "Title": "The Matrix",
            "Year": "1999",
            "Runtime": "136 min",
            "Genre": "Action, Sci-Fi",
            "Director": "Lana Wachowski, Lilly Wachowski",
            "Writer": "Lilly Wachowski, Lana Wachowski",
            "Actors": "Keanu Reeves, Laurence Fishburne, Carrie-Anne Moss",
            "Plot": "A computer hacker learns about the true nature of reality.",
        }

        mock_client.get.return_value = omdb_response

        client = MovieMetadataClient(
            provider="omdb", tmdb_api_key="", omdb_api_key="test_key"
        )
        result = client.fetch_movie_metadata("The Matrix")

        assert result is not None
        assert result.title == "The Matrix"
        assert result.year == 1999
        assert result.duration == 136
        assert result.genres == "Action, Sci-Fi"
        assert "Lana Wachowski" in result.directors
        assert "Keanu Reeves" in result.main_stars

    @patch("backend.services.movie_metadata_client.ENABLE_METADATA_FETCH", True)
    @patch("backend.services.movie_metadata_client.httpx.Client")
    def test_fetch_from_omdb_not_found(self, mock_client_class):
        """Test handling when movie is not found in OMDB."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        omdb_response = MagicMock()
        omdb_response.json.return_value = {
            "Response": "False",
            "Error": "Movie not found!",
        }

        mock_client.get.return_value = omdb_response

        client = MovieMetadataClient(
            provider="omdb", tmdb_api_key="", omdb_api_key="test_key"
        )
        result = client.fetch_movie_metadata("Nonexistent Movie")

        assert result is None

    @patch("backend.services.movie_metadata_client.ENABLE_METADATA_FETCH", True)
    @patch("backend.services.movie_metadata_client.httpx.Client")
    def test_caching(self, mock_client_class):
        """Test that results are cached to avoid redundant API calls."""
        from backend.services.movie_metadata_client import _metadata_cache

        # Clear cache
        _metadata_cache.clear()

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        search_response = MagicMock()
        search_response.json.return_value = {
            "results": [{"id": 603, "title": "The Matrix"}]
        }

        details_response = MagicMock()
        details_response.json.return_value = {
            "title": "The Matrix",
            "overview": "Test",
            "runtime": 136,
            "genres": [],
            "credits": {"cast": [], "crew": []},
        }

        mock_client.get.side_effect = [search_response, details_response]

        client = MovieMetadataClient(
            provider="tmdb", tmdb_api_key="test_key", omdb_api_key=""
        )

        # First call - should hit API
        result1 = client.fetch_movie_metadata("The Matrix")
        assert result1 is not None
        assert mock_client.get.call_count == 2

        # Second call - should use cache
        result2 = client.fetch_movie_metadata("The Matrix")
        assert result2 is not None
        assert mock_client.get.call_count == 2  # No additional calls

        # Clear cache for other tests
        _metadata_cache.clear()

    @patch("backend.services.movie_metadata_client.ENABLE_METADATA_FETCH", True)
    @patch("backend.services.movie_metadata_client.httpx.Client")
    def test_http_error_handling(self, mock_client_class):
        """Test handling of HTTP errors."""
        import httpx

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # Simulate HTTP error
        mock_client.get.side_effect = httpx.HTTPStatusError(
            "API Error", request=MagicMock(), response=MagicMock(status_code=401)
        )

        client = MovieMetadataClient(
            provider="tmdb", tmdb_api_key="invalid_key", omdb_api_key=""
        )
        result = client.fetch_movie_metadata("The Matrix")

        assert result is None


class TestFetchMovieMetadataFunction:
    """Test the convenience fetch_movie_metadata function."""

    @patch("backend.services.movie_metadata_client.get_metadata_client")
    def test_fetch_movie_metadata(self, mock_get_client):
        """Test that the convenience function calls the client correctly."""
        mock_client = MagicMock()
        mock_metadata = MovieMetadata(title="Test Movie", description="Test", year=2020)
        mock_client.fetch_movie_metadata.return_value = mock_metadata
        mock_get_client.return_value = mock_client

        result = fetch_movie_metadata("Test Movie", year=2020)

        assert result == mock_metadata
        # Check that it was called with the correct arguments (as positional args)
        mock_client.fetch_movie_metadata.assert_called_once_with("Test Movie", 2020)
