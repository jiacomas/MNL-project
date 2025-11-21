import pytest

from backend.services import analytics_service


def _assert_or_skip_for_empty_rows(rows, skip_message: str) -> None:
    """
    Helper to skip tests when the local environment lacks review data.
    """
    if not rows:
        pytest.skip(skip_message)


@pytest.mark.integration
def test_search_case_insensitive() -> None:
    """
    Searching by lowercase query should match titles regardless of case.
    Example: 'avengers' matches 'Avengers Endgame' or 'The Avengers'.
    """
    rows = analytics_service.search_reviews_by_title("avengers")

    _assert_or_skip_for_empty_rows(
        rows, "No matching reviews for 'avengers' found in test data"
    )

    assert isinstance(rows, list)
    for row in rows:
        assert "avengers" in row["movie_title"].lower()


@pytest.mark.integration
def test_sort_by_rating_desc() -> None:
    """
    Sorting by rating descending should produce ratings from high → low.
    """
    rows = analytics_service.search_reviews_by_title("", sort_by="rating", order="desc")

    if len(rows) < 2:
        pytest.skip("Not enough reviews to test sorting")

    ratings = [row["rating"] or 0 for row in rows]
    assert ratings == sorted(ratings, reverse=True)


@pytest.mark.integration
def test_write_reviews_csv(tmp_path) -> None:
    """
    Writing review search results to CSV should produce a file
    containing the correct header row.
    """
    rows = analytics_service.search_reviews_by_title("joker")

    _assert_or_skip_for_empty_rows(
        rows, "No matching reviews for 'joker' found in test data"
    )

    filename = "test_joker_export.csv"
    csv_path = analytics_service.write_reviews_csv(rows, filename=filename)

    assert csv_path.exists()

    lines = csv_path.read_text(encoding="utf-8").splitlines()
    assert lines
    assert lines[0] == "id,movie_title,rating,created_at,user_id"
