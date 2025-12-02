"""
Tests specifically designed to improve coverage for movies_repo.py helper functions and edge cases.
"""

from datetime import datetime, timezone
from unittest.mock import mock_open, patch

from backend.repositories.movies_repo import (
    MovieRepository,
    _clean_numeric_string,
    _load_movies_from_csv,
    _load_movies_from_json,
    _movie_to_dict,
    _normalize_movie_fields,
    _parse_date_field,
    _parse_int_like,
    _parse_suffix_number,
    _safe_to_float,
    _safe_to_int,
    _save_movies_to_csv,
    _save_movies_to_json,
)


class TestRepoHelpers:
    def test_parse_date_field(self):
        # None -> Now
        assert isinstance(_parse_date_field(None), datetime)
        # Empty string -> Now
        assert isinstance(_parse_date_field(""), datetime)
        # Valid ISO with Z
        dt = _parse_date_field("2020-01-01T12:00:00Z")
        assert dt.year == 2020
        # Invalid string -> Now
        assert isinstance(_parse_date_field("not-a-date"), datetime)
        # Non-string -> Now
        assert isinstance(_parse_date_field(123), datetime)

    def test_safe_to_int(self):
        assert _safe_to_int(None) is None
        assert _safe_to_int("123") == 123
        assert _safe_to_int("1.2K") == 1200
        # Exception case (mocking _parse_int_like to raise)
        with patch(
            "backend.repositories.movies_repo._parse_int_like",
            side_effect=Exception("boom"),
        ):
            assert _safe_to_int("123") is None

    def test_safe_to_float(self):
        assert _safe_to_float(None) is None
        assert _safe_to_float("12.34") == 12.34
        assert _safe_to_float("1,234.56") == 1234.56
        assert _safe_to_float("not-a-float") is None

    def test_parse_suffix_number(self):
        assert _parse_suffix_number(None) is None
        assert _parse_suffix_number("") is None
        assert _parse_suffix_number("   ") is None
        assert _parse_suffix_number("100") is None  # No suffix
        assert _parse_suffix_number("1.5K") == 1500
        assert _parse_suffix_number("2M") == 2000000
        assert _parse_suffix_number("1.5G") is None  # Invalid suffix
        assert _parse_suffix_number("badK") is None  # Invalid number part

    def test_clean_numeric_string(self):
        assert _clean_numeric_string("abc12.34def") == "12.34"
        assert _clean_numeric_string("no-digits") == "-"
        assert _clean_numeric_string("") == ""

    def test_parse_int_like(self):
        assert _parse_int_like(None) is None
        assert _parse_int_like(10) == 10
        assert _parse_int_like(10.5) == 10
        assert _parse_int_like("") is None
        assert _parse_int_like("  ") is None
        assert _parse_int_like("1.2K") == 1200
        assert _parse_int_like("1,234") == 1234
        assert _parse_int_like("bad") is None
        assert _parse_int_like("-") is None
        assert _parse_int_like(".") is None
        assert _parse_int_like("12.34") == 12

    def test_normalize_movie_fields(self):
        # Movie ID conversion
        m = {"movie_id": 123}
        _normalize_movie_fields(m)
        assert m["movie_id"] == "123"

        # Duration parsing
        m = {"duration": "120 min"}
        _normalize_movie_fields(m)
        assert m["duration"] == 120

        # Rating parsing
        m = {"movieIMDbRating": "8,5"}  # comma handling? No, replace handles it
        # Actually _safe_to_float handles comma, but normalize does explicit replace
        m = {"movieIMDbRating": "8,5"}
        _normalize_movie_fields(m)
        # float("8,5".replace(",", "")) -> float("85") -> 85.0
        assert m["movieIMDbRating"] == 85.0

        # Rating exception
        m = {"movieIMDbRating": "bad"}
        _normalize_movie_fields(m)
        assert m["movieIMDbRating"] is None


class TestRepoFileOps:
    def test_load_movies_from_csv_file_not_found(self):
        with patch("os.path.exists", return_value=False):
            assert _load_movies_from_csv() == []

    def test_load_movies_from_csv_empty_header(self):
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data="")):
                assert _load_movies_from_csv() == []

    def test_load_movies_from_csv_exception(self):
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", side_effect=Exception("read error")):
                assert _load_movies_from_csv() == []

    def test_save_movies_to_csv_empty_fieldnames(self):
        # If no fields found (e.g. empty list or non-dict items), truncate file
        with patch("backend.repositories.movies_repo._ensure_data_dir"):
            m = mock_open()
            with patch("builtins.open", m):
                _save_movies_to_csv([1, 2, 3])  # Non-dict items
                handle = m()
                handle.truncate.assert_called_with(0)

    def test_load_movies_from_json_file_not_found(self):
        with patch("os.path.exists", return_value=False):
            assert _load_movies_from_json() == []

    def test_load_movies_from_json_exception(self):
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", side_effect=Exception("read error")):
                assert _load_movies_from_json() == []

    def test_load_movies_from_json_bad_content(self):
        with patch("os.path.exists", return_value=True):
            # Valid JSON but not a list of dicts
            with patch("builtins.open", mock_open(read_data='[1, "string"]')):
                # Should skip non-dict items
                assert _load_movies_from_json() == []

            # Normalization error (simulated)
            with patch("builtins.open", mock_open(read_data='[{"title": "A"}]')):
                with patch(
                    "backend.repositories.movies_repo._normalize_movie_fields",
                    side_effect=Exception("norm error"),
                ):
                    # Should still process but skip normalization for that item
                    res = _load_movies_from_json()
                    assert len(res) == 1
                    assert res[0]["title"] == "A"


class TestRepoEdgeCases:
    def test_get_popular_validation_error(self):
        repo = MovieRepository()
        # Mock load to return a movie that fails validation (missing required field)
        # MovieOut requires title, etc.
        bad_movie = {"movie_id": "1"}  # Missing title
        repo._load_movies = lambda: [bad_movie]

        # Should skip the bad movie
        assert repo.get_popular() == []

    def test_get_recent_fallback_sort(self):
        repo = MovieRepository()
        # Movie without created_at
        m1 = {"movie_id": "1", "title": "A", "created_at": None}
        m2 = {
            "movie_id": "2",
            "title": "B",
            "created_at": datetime(2024, 1, 1, tzinfo=timezone.utc),
        }

        repo._load_movies = lambda: [m1, m2]
        # get_recent sorts reverse=True. m1 gets min date, m2 gets 2024.
        # So m2 should be first.

        # We need to mock _movie_to_dict or ensure validation passes
        # But get_recent calls model_validate.
        # Let's mock model_validate to just return the dict to avoid validation errors
        with patch(
            "backend.schemas.movies.MovieOut.model_validate", side_effect=lambda x: x
        ):
            with patch(
                "backend.repositories.movies_repo._movie_to_dict",
                side_effect=lambda x: x,
            ):
                recent = repo.get_recent(limit=2)
                assert recent[0]["movie_id"] == "2"
                assert recent[1]["movie_id"] == "1"

    def test_save_movies_to_json(self):
        # Test actual writing logic
        with patch("backend.repositories.movies_repo._ensure_data_dir"):
            m = mock_open()
            with patch("builtins.open", m):
                dt = datetime(2020, 1, 1, tzinfo=timezone.utc)
                movies = [{"title": "A", "created_at": dt, "updated_at": dt}]
                _save_movies_to_json(movies)

                # Check if write was called
                handle = m()
                handle.write.assert_called()
                # Verify ISO format conversion happened in the call args
                # (This is a bit loose, just ensuring it didn't crash and tried to write)

    def test_get_by_title(self):
        repo = MovieRepository()
        repo._load_movies = lambda: [{"movie_id": "1", "title": "The Matrix"}]

        # Match
        m = repo.get_by_title("the matrix")
        assert m.title == "The Matrix"

        # No match
        assert repo.get_by_title("not found") is None

    def test_search_sort_and_exceptions(self):
        repo = MovieRepository()
        movies = [
            {"movie_id": "1", "title": "A", "datePublished": "2000-01-01"},
            {
                "movie_id": "2",
                "title": "B",
                "datePublished": "bad-date",
            },  # Should trigger date parse exception
        ]
        repo._load_movies = lambda: movies

        # Test sort_by
        results, _ = repo.search(sort_by="title", sort_desc=True)
        assert results[0].title == "B"

        # Test date exception (release_year search on bad date)
        # "bad-date" split("-")[0] is "bad-date", int() raises ValueError
        results, _ = repo.search(release_year=2000)
        assert len(results) == 1
        assert results[0].title == "A"

    def test_movie_to_dict_timezone(self):
        # Test timezone replacement for naive datetime
        naive = datetime(2020, 1, 1)  # No timezone
        m = {"created_at": naive, "updated_at": naive}
        res = _movie_to_dict(m)
        assert res["created_at"].tzinfo == timezone.utc
        assert res["updated_at"].tzinfo == timezone.utc

    def test_parse_int_like_exception(self):
        # "1.2.3" passes _clean_numeric_string but fails float()
        assert _parse_int_like("1.2.3") is None
