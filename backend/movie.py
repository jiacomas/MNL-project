import json
from typing import List, Dict, Any


class Movie:
    def __init__(self, data_file: str = "data/movies.json"):
        """
        Initialize Movie class

        Args:
            data_file: Path to the movies JSON data file
        """
        self.data_file = data_file

    def _load_movies(self) -> List[Dict[str, Any]]:
        """Load all movies data from JSON file"""
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)
                return data.get("movies", [])
        except (FileNotFoundError, json.JSONDecodeError):
            # Return empty list if file doesn't exist or has invalid format
            return []

    def searchByTitle(self, query: str) -> List[Dict[str, Any]]:
        """
        Search movies by title

        Args:
            query: Search keyword

        Returns:
            List of matching movies
        """
        if not query:
            return []

        movies = self._load_movies()
        query_lower = query.lower()

        # Case-insensitive search
        results = []
        for movie in movies:
            if query_lower in movie.get("title", "").lower():
                results.append(movie)

        return results

    def filterByGenre(self, genre: str) -> List[Dict[str, Any]]:
        """
        Filter movies by genre

        Args:
            genre: Movie genre to filter by

        Returns:
            List of movies in the specified genre
        """
        if not genre:
            return []

        movies = self._load_movies()
        genre_lower = genre.lower()

        results = []
        for movie in movies:
            if genre_lower == movie.get("genre", "").lower():
                results.append(movie)

        return results

    def sortBy(self, attribute: str, ascending: bool = True) -> List[Dict[str, Any]]:
        """
        Sort movies by specified attribute

        Args:
            attribute: Attribute to sort by (title, releaseYear, runtime)
            ascending: True for ascending order, False for descending

        Returns:
            Sorted list of movies
        """
        movies = self._load_movies()

        # Simple sorting implementation
        if attribute == "title":
            sorted_movies = sorted(movies, key=lambda x: x.get("title", "").lower(), reverse=not ascending)
        else:
            sorted_movies = sorted(movies, key=lambda x: x.get(attribute, 0), reverse=not ascending)

        return sorted_movies

    def enrichMetadata(self, movie_data: Dict[str, Any], api_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich movie metadata with API data

        Args:
            movie_data: Original movie data
            api_data: Data from external API

        Returns:
            Movie data with enriched metadata
        """
        # Create copy to avoid modifying original data
        enriched = movie_data.copy()

        # Ensure metadata field exists
        if "metadata" not in enriched:
            enriched["metadata"] = {}

        # Merge metadata without overwriting core fields
        for key, value in api_data.items():
            if key not in ["movie_id", "title", "releaseYear"]:
                enriched["metadata"][key] = value

        return enriched

    def getDetails(self, movie_id: str) -> Dict[str, Any]:
        """
        Get movie details by ID

        Args:
            movie_id: Unique movie identifier

        Returns:
            Movie details dictionary, empty dict if not found
        """
        movies = self._load_movies()

        for movie in movies:
            if movie.get("movie_id") == movie_id:
                return movie

        return {}


