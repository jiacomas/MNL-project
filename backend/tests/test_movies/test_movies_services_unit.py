"""
Unit tests for Movies Service (aligned with simplified repo)
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from backend.schemas.movies import (
    MovieListResponse,
    MovieOut,
    MovieSearchFilters,
    MovieUpdate,
)
from backend.services.movies_service import (
    create_movie,
    delete_movie,
    get_movie,
    get_movie_stats,
    get_movies,
    get_popular_movies,
    get_recent_movies,
    search_movies,
    update_movie,
)
from backend.tests.test_movies.conftest import create_valid_movie_create


@pytest.fixture
def mock_repo():
    """Mock MovieRepository."""
    mock = MagicMock()
    mock.search = MagicMock()
    mock.get_all.return_value = ([], 0)
    return mock


@pytest.fixture
def sample_movie_out():
    """Sample MovieOut."""
    return MovieOut(
        movie_id="tt011",
        title="Sample Movie",
        movieGenres="Action",
        datePublished="2000-01-01",
        movieIMDbRating=8.5,
        duration=120,
        directors="Director X",
        mainStars="Actor Y",
        description="A plot.",
        poster_url="url",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        review_count=5,
    )


class TestMoviesServiceUnit:
    def test_get_movies_correct_call(self, mock_repo, sample_movie_out):
        mock_repo.get_all.return_value = ([sample_movie_out], 10)
        res = get_movies(
            page=2, page_size=50, sort_by="title", sort_desc=True, repo=mock_repo
        )
        mock_repo.get_all.assert_called_once_with(
            skip=50, limit=50, sort_by="title", sort_desc=True
        )
        assert isinstance(res, MovieListResponse)
        assert res.page == 2
        assert res.page_size == 50

    @pytest.mark.parametrize("page,page_size", [(0, 10), (1, 0), (1, 201)])
    def test_get_movies_invalid_pagination(self, mock_repo, page, page_size):
        with pytest.raises(HTTPException):
            get_movies(page=page, page_size=page_size, repo=mock_repo)

    def test_get_movies_invalid_sort_by(self, mock_repo):
        with pytest.raises(HTTPException):
            get_movies(page=1, page_size=10, sort_by="bad_field", repo=mock_repo)

    def test_get_popular_movies_valid(self, mock_repo, sample_movie_out):
        mock_repo.get_popular.return_value = [sample_movie_out]
        res = get_popular_movies(limit=5, repo=mock_repo)
        mock_repo.get_popular.assert_called_once_with(limit=5)
        assert res[0].movie_id == sample_movie_out.movie_id

    @pytest.mark.parametrize("limit", [0, 51])
    def test_get_popular_movies_invalid(self, mock_repo, limit):
        with pytest.raises(HTTPException):
            get_popular_movies(limit=limit, repo=mock_repo)

    def test_get_recent_movies_valid(self, mock_repo, sample_movie_out):
        mock_repo.get_recent.return_value = [sample_movie_out]
        res = get_recent_movies(limit=10, repo=mock_repo)
        mock_repo.get_recent.assert_called_once_with(limit=10)
        assert res[0].title == sample_movie_out.title

    @pytest.mark.parametrize("limit", [0, 51])
    def test_get_recent_movies_invalid(self, mock_repo, limit):
        with pytest.raises(HTTPException):
            get_recent_movies(limit=limit, repo=mock_repo)

    def test_search_movies_correct_call(self, mock_repo, sample_movie_out):
        mock_repo.search.return_value = ([sample_movie_out], 1)
        filters = MovieSearchFilters(title="shaw", genre="Drama", release_year=1994)
        res = search_movies(filters=filters, page=2, page_size=10, repo=mock_repo)
        mock_repo.search.assert_called_once_with(
            title="shaw",
            genre="Drama",
            release_year=1994,
            skip=10,
            limit=10,
            sort_by=None,
            sort_desc=False,
        )
        assert res.items[0].title == sample_movie_out.title

    def test_search_movies_with_sorting(self, mock_repo, sample_movie_out):
        mock_repo.search.return_value = ([sample_movie_out], 1)
        filters = MovieSearchFilters(title="shaw", genre="Drama", release_year=1994)

        res = search_movies(
            filters=filters,
            page=1,
            page_size=10,
            sort_by="rating",
            sort_desc=True,
            repo=mock_repo,
        )

        mock_repo.search.assert_called_once_with(
            title="shaw",
            genre="Drama",
            release_year=1994,
            skip=0,
            limit=10,
            sort_by="rating",
            sort_desc=True,
        )
        assert res.items[0].title == sample_movie_out.title

    def test_search_movies_invalid_sort_by(self, mock_repo):
        filters = MovieSearchFilters()
        with pytest.raises(HTTPException):
            search_movies(
                filters=filters,
                page=1,
                page_size=10,
                sort_by="not_a_field",
                repo=mock_repo,
            )

    def test_get_movie_stats(self, mock_repo):
        movie1 = MovieOut(
            movie_id="1",
            title="A",
            movieGenres="Drama, Comedy",
            movieIMDbRating=10.0,
            datePublished="2000-01-01",
            duration=90,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        movie2 = MovieOut(
            movie_id="2",
            title="B",
            movieGenres="Drama",
            movieIMDbRating=8.0,
            datePublished="2000-01-01",
            duration=90,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        movie3 = MovieOut(
            movie_id="3",
            title="C",
            movieGenres="Action",
            movieIMDbRating=6.0,
            datePublished="2024-01-01",
            duration=90,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        mock_repo.get_all.side_effect = [([movie1, movie2, movie3], 3), ([], 100)]
        stats = get_movie_stats(repo=mock_repo)
        assert stats["total_movies"] == 100
        assert stats["average_rating"] == 8.0
        assert ("Drama", 2) in stats["top_genres"]
        assert stats["year_range"]["max"] == 2024

    def test_get_movie_not_found(self, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(HTTPException):
            get_movie("bad", repo=mock_repo)

    def test_create_movie_admin_only(self, mock_repo):
        with pytest.raises(HTTPException):
            create_movie(create_valid_movie_create(), is_admin=False, repo=mock_repo)

    def test_update_movie_not_found(self, mock_repo):
        mock_repo.update.return_value = None
        with pytest.raises(HTTPException):
            update_movie("bad", MovieUpdate(title="x"), is_admin=True, repo=mock_repo)

    def test_delete_movie_not_found(self, mock_repo):
        mock_repo.delete.return_value = False
        with pytest.raises(HTTPException):
            delete_movie("bad", is_admin=True, repo=mock_repo)

    def test_delete_movie_admin_only(self, mock_repo):
        with pytest.raises(HTTPException):
            delete_movie("id", is_admin=False, repo=mock_repo)

    def test_create_movie_repo_error(self, mock_repo):
        mock_repo.create.side_effect = ValueError("constraint fail")
        with pytest.raises(HTTPException):
            create_movie(create_valid_movie_create(), is_admin=True, repo=mock_repo)

    def test_movie_lifecycle(self, mock_repo, sample_movie_out):
        updated = sample_movie_out.model_copy(update={"title": "Updated Title"})
        mock_repo.create.return_value = sample_movie_out
        mock_repo.get_by_id.return_value = sample_movie_out
        mock_repo.update.return_value = updated
        mock_repo.delete.return_value = True

        assert create_movie(create_valid_movie_create(), is_admin=True, repo=mock_repo)
        assert get_movie("tt011", repo=mock_repo)
        assert (
            update_movie(
                "tt011",
                MovieUpdate(title="Updated Title"),
                is_admin=True,
                repo=mock_repo,
            ).title
            == "Updated Title"
        )
        delete_movie("tt011", is_admin=True, repo=mock_repo)

    def test_update_movie_admin_only(self, mock_repo):
        """Test that update_movie requires admin privileges."""
        with pytest.raises(HTTPException) as exc:
            update_movie("id", MovieUpdate(title="x"), is_admin=False, repo=mock_repo)
        assert exc.value.status_code == 403

    def test_get_movie_stats_empty(self, mock_repo):
        """Test get_movie_stats with no movies."""
        mock_repo.get_all.side_effect = [([], 0), ([], 0)]
        stats = get_movie_stats(repo=mock_repo)
        assert stats["total_movies"] == 0
        assert stats["average_rating"] == 0
        assert stats["top_genres"] == []
        assert stats["year_range"] == {"min": 0, "max": 0}

    def test_collect_ratings_edge_cases(self):
        """Test _collect_ratings with None/invalid ratings."""
        from backend.services.movies_service import _collect_ratings

        m1 = MagicMock()
        m1.movieIMDbRating = None
        m2 = MagicMock()
        m2.movieIMDbRating = "bad"  # Should cause float() exception
        m3 = MagicMock()
        m3.movieIMDbRating = 8.5

        ratings = _collect_ratings([m1, m2, m3])
        assert len(ratings) == 1
        assert ratings[0] == 8.5

    def test_aggregate_genres_edge_cases(self):
        """Test _aggregate_genres with None/empty/pipe/comma."""
        from backend.services.movies_service import _aggregate_genres

        m1 = MagicMock()
        m1.movieGenres = None
        m2 = MagicMock()
        m2.movieGenres = "Action|Sci-Fi"
        m3 = MagicMock()
        m3.movieGenres = "Comedy, Drama"
        m4 = MagicMock()
        m4.movieGenres = ""

        counts = _aggregate_genres([m1, m2, m3, m4])
        assert counts["Action"] == 1
        assert counts["Sci-Fi"] == 1
        assert counts["Comedy"] == 1
        assert counts["Drama"] == 1

    def test_derive_years_edge_cases(self):
        """Test _derive_years with invalid dates."""
        from backend.services.movies_service import _derive_years

        m1 = MagicMock()
        m1.datePublished = None
        m2 = MagicMock()
        m2.datePublished = "2020-01-01"
        m3 = MagicMock()
        m3.datePublished = "bad"  # Too short/invalid
        m4 = MagicMock()
        m4.datePublished = "199"  # Too short

        years = _derive_years([m1, m2, m3, m4])
        assert len(years) == 1
        assert years[0] == 2020

    def test_search_movies_invalid_pagination(self, mock_repo):
        """Test search_movies pagination validation."""
        filters = MovieSearchFilters()
        with pytest.raises(HTTPException):
            search_movies(filters, page=0, repo=mock_repo)
        with pytest.raises(HTTPException):
            search_movies(filters, page_size=201, repo=mock_repo)

    def test_derive_years_exception(self):
        """Test _derive_years with string that is long enough but not an int."""
        from backend.services.movies_service import _derive_years

        m = MagicMock()
        m.datePublished = "abcd"  # len 4, but int("abcd") raises ValueError
        years = _derive_years([m])
        assert years == []
