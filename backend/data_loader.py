# backend/data_loader.py

"""
Utilities for loading movie data from Kaggle into the local data directory.
"""

import os
import shutil
from pathlib import Path

import kagglehub

from backend import settings
from backend.__local_use__ import convert_movies_json_to_csv, create_movies_data


def load_movies_from_kaggle() -> dict:
    """
    Download dataset from Kaggle, copy CSV/JSON files into MOVIE_DATA_PATH,
    generate movies.json and movies.csv.

    Returns a summary dict with basic stats.
    """
    # read dataset & target path from centralized settings
    dataset_slug = settings.KAGGLE_DATASET
    target_root = settings.MOVIE_DATA_PATH

    # Download dataset from Kaggle to cache
    cache_root = Path(kagglehub.dataset_download(dataset_slug))

    # Copy relevant files to target location
    target_root.mkdir(parents=True, exist_ok=True)
    copied = 0
    for dirpath, _, filenames in os.walk(cache_root):
        for filename in filenames:
            # only keep CSV/JSON
            if not filename.lower().endswith((".csv", ".json")):
                continue
            src = Path(dirpath) / filename
            rel = src.relative_to(cache_root)  # e.g. "Joker/movieReviews.csv"
            dst = target_root / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            copied += 1

    # Create movies data JSON
    create_movies_data.main()

    # Convert movies JSON to CSV
    convert_movies_json_to_csv.main()

    return {
        "files_copied": copied,
        "target_root": str(target_root),
    }
