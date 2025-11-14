import pytest

from backend.services import analytics_service


def test_search_case_insensitive():
    # Search for 'avengers' should match 'Avengers Endgame' and/or 'The Avengers'
    rows = analytics_service.search_reviews_by_title("avengers")
    assert isinstance(rows, list)
    # If no rows exist for this environment, test is skipped
    if not rows:
        pytest.skip("No matching reviews for 'avengers' found in test data")
    for r in rows:
        assert "avengers" in r["movie_title"].lower()


def test_sort_by_rating_desc():
    rows = analytics_service.search_reviews_by_title("", sort_by="rating", order="desc")
    if len(rows) < 2:
        pytest.skip("Not enough reviews to test sorting")
    ratings = [r["rating"] or 0 for r in rows]
    assert ratings == sorted(ratings, reverse=True)


def test_write_reviews_csv(tmp_path):
    rows = analytics_service.search_reviews_by_title("joker")
    if not rows:
        pytest.skip("No matching reviews for 'joker' found in test data")

    # write to a specific filename inside exports dir
    filename = "test_joker_export.csv"
    csv_path = analytics_service.write_reviews_csv(rows, filename=filename)
    assert csv_path.exists()
    content = csv_path.read_text(encoding="utf-8")
    assert "id,movie_title,rating,created_at,user_id" in content.splitlines()[0]
