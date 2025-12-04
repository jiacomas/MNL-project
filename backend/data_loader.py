# backend/data_loader.py

"""
Utilities for loading movie data from Kaggle into the local data directory.
"""

import csv
import os
import shutil
from pathlib import Path

import kagglehub

from backend import settings
from backend.__local_use__ import convert_movies_json_to_csv, create_movies_data


def _fix_kaggle_csv_fields(root: Path):
    """
    Iterate through all CSVs under MOVIE_DATA_PATH and standardize:
    User -> username
    """
    for csv_file in root.rglob("*.csv"):
        with open(csv_file, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames.copy()

        # if "User" exists, rename it
        if "User" in fieldnames and "username" not in fieldnames:
            new_fieldnames = ["username" if f == "User" else f for f in fieldnames]
        else:
            continue  # no need to modify this file

        # Write updated CSV
        rows = []
        with open(csv_file, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if "User" in row and "username" not in row:
                    row["username"] = row.pop("User")
                rows.append(row)

        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=new_fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        print(f"[FIELD FIX] Updated User -> username in {csv_file}")


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

    # Fix CSV field names for consistency
    _fix_kaggle_csv_fields(target_root)

    # Create movies data JSON
    create_movies_data.main()

    # Convert movies JSON to CSV
    convert_movies_json_to_csv.main()

    return {
        "files_copied": copied,
        "target_root": str(target_root),
    }
