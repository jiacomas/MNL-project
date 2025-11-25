from __future__ import annotations

import os
from pathlib import Path

# Project layout
ROOT = Path(__file__).resolve().parent.parent
ROOT_DATA_DIR = Path(os.getenv("ROOT_DATA_DIR", str(ROOT / "backend" / "data")))

# Admin-configurable session timeout (minutes)
SESSION_INACTIVITY_TIMEOUT_MINUTES = int(
    os.getenv("SESSION_INACTIVITY_TIMEOUT_MINUTES", "15")
)

# JWT settings (kept here for convenience)
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-key")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

# File paths used by services (can be overridden via env)
ITEMS_FILE = Path(os.getenv("ITEMS_FILE", str(ROOT_DATA_DIR / "items.json")))
REVIEWS_FILE = Path(os.getenv("REVIEWS_FILE", str(ROOT_DATA_DIR / "reviews.json")))
SYNC_LOG_FILE = Path(
    os.getenv("SYNC_LOG_FILE", str(ROOT_DATA_DIR / "external_sync_log.json"))
)

# External API settings
EXTERNAL_API_BASE_URL = os.getenv(
    "EXTERNAL_API_BASE_URL", "https://example.com/movie-api"
)
EXTERNAL_API_KEY_ENV = os.getenv("EXTERNAL_API_KEY_ENV", "MOVIE_API_KEY")

# Kaggle / data import defaults
KAGGLE_DATASET = os.getenv("KAGGLE_DATASET", "sadmadlad/imdb-user-reviews")
MOVIE_DATA_PATH = Path(os.getenv("MOVIE_DATA_PATH", str(ROOT_DATA_DIR / "movies")))

# Bookmarks
BOOKMARKS_PATH = Path(
    os.getenv("BOOKMARKS_PATH", str(ROOT_DATA_DIR / "bookmarks.json"))
)
BOOKMARKS_EXPORT_DIR = Path(
    os.getenv("BOOKMARKS_EXPORT_DIR", str(ROOT_DATA_DIR / "exports"))
)

# Movies repo paths
MOVIES_CSV_PATH = Path(
    os.getenv("MOVIES_CSV_PATH", str(ROOT_DATA_DIR / "movies" / "movies.csv"))
)
MOVIES_JSON_PATH = Path(
    os.getenv("MOVIES_JSON_PATH", str(ROOT_DATA_DIR / "movies" / "movies.json"))
)
EXTERNAL_METADATA_DIR = Path(
    os.getenv(
        "EXTERNAL_METADATA_DIR", str(ROOT_DATA_DIR / "movies" / "external_metadata")
    )
)
