"""
Download the latest version of the IMDB user reviews dataset
using kagglehub and store it in the local data directory.
"""

import os
import shutil

# backend/data.py
# backend/data.py
from pathlib import Path

import kagglehub

from backend import settings

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
        if not filename.lower().endswith((".csv", ".json")):
            continue
        src = Path(dirpath) / filename
        rel = src.relative_to(cache_root)  # e.g. "Joker/movieReviews.csv"
        dst = target_root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        copied += 1

print(f"Copied {copied} files to: {target_root}")
