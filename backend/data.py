# backend/data.py
from pathlib import Path
import os, shutil
import kagglehub
from dotenv import load_dotenv

# read .env
load_dotenv()
dataset_slug = os.getenv("KAGGLE_DATASET", "sadmadlad/imdb-user-reviews")
target_root = Path(os.getenv("MOVIE_DATA_PATH", "backend/app/data/movies"))

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
        rel = src.relative_to(cache_root)      # e.g. "Joker/movieReviews.csv"
        dst = target_root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        copied += 1

print(f"Copied {copied} files to: {target_root}")
