"""
Integration tests for movie schemas working together.
"""
import pytest
from datetime import datetime, timezone
from schemas.movies import MovieCreate, MovieUpdate, MovieOut, MovieSearchFilters, MovieListResponse


@pytest.mark.integration
@pytest.mark.slow
class TestMovieSchemasIntegration:
    """Integration tests for movie schemas working together.

    These tests verify that multiple schemas work correctly together
    in real-world scenarios and workflows.
    """

    @pytest.mark.integration
    def test_create_to_output_flow(self):
        """Integration test: Verify MovieCreate to MovieOut conversion workflow."""
        # Create a movie using MovieCreate
        create_data = {
            "movie_id": "tt0111161",
            "title": "The Shawshank Redemption",
            "genre": "Drama",
            "release_year": 1994,
            "rating": 9.3,
            "runtime": 142
        }
        movie_create = MovieCreate(**create_data)

        # Simulate converting to MovieOut (as would happen in service layer)
        now = datetime.now(timezone.utc)
        movie_out_data = {
            **movie_create.model_dump(),
            "created_at": now,
            "updated_at": now,
            "review_count": 2500000
        }
        movie_out = MovieOut(**movie_out_data)

        # Verify data consistency between create and output schemas
        assert movie_out.movie_id == movie_create.movie_id
        assert movie_out.title == movie_create.title
        assert movie_out.genre == movie_create.genre
        assert movie_out.release_year == movie_create.release_year
        assert movie_out.rating == movie_create.rating
        assert movie_out.runtime == movie_create.runtime

    @pytest.mark.integration
    def test_update_workflow(self):
        """Integration test: Verify complete movie update workflow."""
        # Create original movie
        original_data = {
            "movie_id": "tt0111161",
            "title": "Original Title",
            "genre": "Drama",
            "release_year": 1994,
            "rating": 8.0,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "review_count": 1000
        }
        original_movie = MovieOut(**original_data)

        # Create update request
        update_data = {
            "title": "Updated Title",
            "rating": 9.0
        }
        movie_update = MovieUpdate(**update_data)

        # Simulate applying update (as would happen in service layer)
        updated_data = original_data.copy()
        for field, value in movie_update.model_dump(exclude_unset=True).items():
            if value is not None:
                updated_data[field] = value
        updated_data["updated_at"] = datetime.now(timezone.utc)

        updated_movie = MovieOut(**updated_data)

        # Verify updates were applied correctly and unchanged fields preserved
        assert updated_movie.title == "Updated Title"
        assert updated_movie.rating == 9.0
        assert updated_movie.genre == original_movie.genre  # Unchanged
        assert updated_movie.release_year == original_movie.release_year  # Unchanged

    @pytest.mark.integration
    def test_search_and_list_integration(self):
        """Integration test: Verify search filters work with list response."""
        # Create search filters
        search_filters = MovieSearchFilters(
            title="shawshank",
            genre="Drama",
            min_year=1990,
            max_year=2000,
            min_rating=8.0
        )

        # Create mock movies that match filters
        now = datetime.now(timezone.utc)
        matching_movies = [
            MovieOut(
                movie_id="tt0111161",
                title="The Shawshank Redemption",
                genre="Drama",
                release_year=1994,
                rating=9.3,
                created_at=now,
                updated_at=now,
                review_count=2500000
            )
        ]

        # Create paginated list response
        list_response = MovieListResponse(
            items=matching_movies,
            total=1,
            page=1,
            page_size=10,
            total_pages=1
        )

        # Verify integration between search filters and response
        assert len(list_response.items) == 1
        movie = list_response.items[0]
        assert search_filters.title.lower() in movie.title.lower()
        assert movie.genre == search_filters.genre
        assert search_filters.min_year <= movie.release_year <= search_filters.max_year
        assert movie.rating >= search_filters.min_rating

    @pytest.mark.integration
    @pytest.mark.slow
    def test_complete_movie_lifecycle(self):
        """Integration test: Complete movie lifecycle from creation to search.

        This test simulates a real-world workflow:
        1. Create multiple movies
        2. Convert to output format (simulating database persistence)
        3. Apply search filters
        4. Return paginated results
        """
        # Step 1: Create multiple movies using MovieCreate schema
        movies_to_create = [
            {
                "movie_id": "tt0111161",
                "title": "The Shawshank Redemption",
                "genre": "Drama",
                "release_year": 1994,
                "rating": 9.3
            },
            {
                "movie_id": "tt0068646",
                "title": "The Godfather",
                "genre": "Crime",
                "release_year": 1972,
                "rating": 9.2
            },
            {
                "movie_id": "tt0468569",
                "title": "The Dark Knight",
                "genre": "Action",
                "release_year": 2008,
                "rating": 9.0
            }
        ]

        created_movies = [MovieCreate(**data) for data in movies_to_create]

        # Step 2: Convert to MovieOut format (simulating database persistence)
        now = datetime.now(timezone.utc)
        movie_out_list = []
        for movie_create in created_movies:
            movie_out_data = {
                **movie_create.model_dump(),
                "created_at": now,
                "updated_at": now,
                "review_count": 1000000
            }
            movie_out_list.append(MovieOut(**movie_out_data))

        # Step 3: Apply search filters
        search_filters = MovieSearchFilters(
            min_year=1990,
            max_year=2010,
            min_rating=9.0
        )

        # Step 4: Filter movies based on search criteria (simulating database query)
        filtered_movies = [
            movie for movie in movie_out_list
            if (search_filters.min_year is None or movie.release_year >= search_filters.min_year) and
               (search_filters.max_year is None or movie.release_year <= search_filters.max_year) and
               (search_filters.min_rating is None or movie.rating >= search_filters.min_rating)
        ]

        # Step 5: Create paginated response
        list_response = MovieListResponse(
            items=filtered_movies,
            total=len(filtered_movies),
            page=1,
            page_size=10,
            total_pages=1
        )

        # Verify final results match expected business logic
        assert len(list_response.items) == 2  # Shawshank Redemption and The Dark Knight
        assert any(movie.movie_id == "tt0111161" for movie in list_response.items)
        assert any(movie.movie_id == "tt0468569" for movie in list_response.items)
        # The Godfather should be filtered out due to release year < 1990
        assert not any(movie.movie_id == "tt0068646" for movie in list_response.items)


@pytest.mark.integration
class TestMovieSchemaDataFlow:
    """Additional integration tests focusing on data flow between schemas."""

    @pytest.mark.integration
    def test_partial_update_workflow(self):
        """Integration test: Verify partial update workflow with null values."""
        # Create original movie with complete data
        original_data = {
            "movie_id": "tt0111161",
            "title": "Original Movie",
            "genre": "Drama",
            "release_year": 1994,
            "rating": 8.5,
            "runtime": 142,
            "director": "Original Director",
            "cast": "Original Cast",
            "plot": "Original plot summary",
            "poster_url": "https://original.com/poster.jpg",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "review_count": 1000
        }
        original_movie = MovieOut(**original_data)

        # Create partial update that sets some fields to None
        update_data = {
            "genre": None,  # Remove genre
            "rating": 9.0,  # Update rating
            "director": "New Director"  # Change director
        }
        movie_update = MovieUpdate(**update_data)

        # Simulate applying partial update
        updated_data = original_data.copy()
        for field, value in movie_update.model_dump(exclude_unset=True).items():
            updated_data[field] = value
        updated_data["updated_at"] = datetime.now(timezone.utc)

        updated_movie = MovieOut(**updated_data)

        # Verify partial update results
        assert updated_movie.genre is None  # Field was set to None
        assert updated_movie.rating == 9.0  # Field was updated
        assert updated_movie.director == "New Director"  # Field was changed
        assert updated_movie.title == original_movie.title  # Unchanged
        assert updated_movie.release_year == original_movie.release_year  # Unchanged