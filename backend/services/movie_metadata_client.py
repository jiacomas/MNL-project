"""
External movie metadata API client.

Supports TMDB (The Movie Database) and OMDB APIs for fetching movie metadata.
"""

from __future__ import annotations

import logging
from typing import Optional

import httpx

from backend.settings import (
    ENABLE_METADATA_FETCH,
    MOVIE_METADATA_API_PROVIDER,
    TMDB_API_BASE_URL,
    TMDB_API_KEY,
)

logger = logging.getLogger(__name__)

# Simple in-memory cache to avoid redundant API calls
_metadata_cache: dict[str, dict] = {}


class MovieMetadata:
    """Container for movie metadata fetched from external APIs."""

    def __init__(
        self,
        title: str,
        description: Optional[str] = None,
        year: Optional[int] = None,
        genres: Optional[str] = None,
        duration: Optional[int] = None,
        directors: Optional[str] = None,
        creators: Optional[str] = None,
        main_stars: Optional[str] = None,
    ):
        self.title = title
        self.description = description
        self.year = year
        self.genres = genres
        self.duration = duration
        self.directors = directors
        self.creators = creators
        self.main_stars = main_stars

    def to_dict(self) -> dict:
        """Convert to dictionary, excluding None values."""
        return {k: v for k, v in self.__dict__.items() if v is not None}


class MovieMetadataClient:
    """Client for fetching movie metadata from external APIs."""

    def __init__(
        self,
        provider: str = MOVIE_METADATA_API_PROVIDER,
        tmdb_api_key: str = TMDB_API_KEY,
    ):
        self.provider = provider.lower()
        self.tmdb_api_key = tmdb_api_key
        self.client = httpx.Client(timeout=10.0)

    def fetch_movie_metadata(
        self, title: str, year: Optional[int] = None
    ) -> Optional[MovieMetadata]:
        """
        Fetch movie metadata by title.

        Args:
            title: Movie title to search for
            year: Optional year to improve search accuracy

        Returns:
            MovieMetadata object if found, None otherwise
        """
        if not ENABLE_METADATA_FETCH:
            logger.debug("Metadata fetching is disabled")
            return None

        # Check cache first
        cache_key = f"{title}_{year or 'none'}".lower()
        if cache_key in _metadata_cache:
            logger.debug(f"Using cached metadata for '{title}'")
            return MovieMetadata(**_metadata_cache[cache_key])

        try:
            if self.provider == "tmdb":
                metadata = self._fetch_from_tmdb(title, year)
            else:
                logger.error(f"Unknown provider: {self.provider}")
                return None

            if metadata:
                # Cache the result
                _metadata_cache[cache_key] = metadata.to_dict()
                logger.info(f"Successfully fetched metadata for '{title}'")
            else:
                logger.warning(f"No metadata found for '{title}'")

            return metadata

        except Exception as e:
            logger.error(f"Error fetching metadata for '{title}': {e}")
            return None

    def _fetch_from_tmdb(
        self, title: str, year: Optional[int] = None
    ) -> Optional[MovieMetadata]:
        """Fetch metadata from TMDB API."""
        if not self.tmdb_api_key or self.tmdb_api_key == "your_api_key_here":
            logger.warning("TMDB API key not configured")
            return None

        try:
            # Step 1: Search for the movie
            search_url = f"{TMDB_API_BASE_URL}/search/movie"
            search_params = {
                "api_key": self.tmdb_api_key,
                "query": title,
            }
            if year:
                search_params["year"] = year

            search_response = self.client.get(search_url, params=search_params)
            search_response.raise_for_status()
            search_data = search_response.json()

            if not search_data.get("results"):
                return None

            # Get the first (most relevant) result
            movie = search_data["results"][0]
            movie_id = movie["id"]

            # Step 2: Get detailed movie information
            details_url = f"{TMDB_API_BASE_URL}/movie/{movie_id}"
            details_params = {
                "api_key": self.tmdb_api_key,
                "append_to_response": "credits",
            }

            details_response = self.client.get(details_url, params=details_params)
            details_response.raise_for_status()
            details = details_response.json()

            # Extract metadata
            return self._parse_tmdb_response(details)

        except httpx.HTTPStatusError as e:
            logger.error(f"TMDB API error: {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"Error fetching from TMDB: {e}")
            return None

    def _parse_tmdb_response(self, details: dict) -> MovieMetadata:
        """Parse TMDB API response into MovieMetadata."""
        # Extract genres
        genres = ", ".join([g["name"] for g in details.get("genres", [])])

        # Extract directors from credits
        directors = []
        credits = details.get("credits", {})
        crew = credits.get("crew", [])
        for person in crew:
            if person.get("job") == "Director":
                directors.append(person.get("name"))

        # Extract main stars (top 5 cast members)
        cast = credits.get("cast", [])
        main_stars = [person.get("name") for person in cast[:5] if person.get("name")]

        # Extract writers/creators
        creators = []
        for person in crew:
            if person.get("job") in ["Writer", "Screenplay", "Story"]:
                name = person.get("name")
                if name and name not in creators:
                    creators.append(name)

        # Extract year from release date
        release_date = details.get("release_date", "")
        year = (
            int(release_date[:4]) if release_date and len(release_date) >= 4 else None
        )

        return MovieMetadata(
            title=details.get("title", ""),
            description=details.get("overview"),
            year=year,
            genres=genres if genres else None,
            duration=details.get("runtime"),
            directors=", ".join(directors) if directors else None,
            creators=", ".join(creators[:3]) if creators else None,  # Limit to top 3
            main_stars=", ".join(main_stars) if main_stars else None,
        )

    def __del__(self):
        """Clean up HTTP client."""
        if hasattr(self, "client"):
            self.client.close()


# Global client instance
_client: Optional[MovieMetadataClient] = None


def get_metadata_client() -> MovieMetadataClient:
    """Get or create the global metadata client instance."""
    global _client
    if _client is None:
        _client = MovieMetadataClient()
    return _client


def fetch_movie_metadata(
    title: str, year: Optional[int] = None
) -> Optional[MovieMetadata]:
    """
    Convenience function to fetch movie metadata.

    Args:
        title: Movie title to search for
        year: Optional year to improve search accuracy

    Returns:
        MovieMetadata object if found, None otherwise
    """
    client = get_metadata_client()
    return client.fetch_movie_metadata(title, year)
