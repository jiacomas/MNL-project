#!/usr/bin/env python3
"""Small script to exercise the movies repository workflow.

This script creates a temporary test data directory (by default
`backend/data/movies_test`), copies any existing movie JSON/CSV into it
(so your real data is preserved), then sets the `MOVIES_CSV_PATH` and
`MOVIES_JSON_PATH` environment variables before importing the repo.

It demonstrates listing movies, creating a new movie, reloading to
verify persistence, and deleting the created movie.

Usage:
    python backend/__local_use__/run_movies_workflow.py

Pass `--outdir` to change the test directory.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "data" / "movies_test"


def prepare_test_dir(outdir: Path) -> Path:
    outdir = outdir.resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    # Try common source locations and copy them if present
    candidates = [
        ROOT / "data" / "movies" / "movies.json",
        ROOT / "data" / "movies.json",
    ]
    for src in candidates:
        if src.exists():
            dst = outdir / "movies.json"
            shutil.copy2(src, dst)
            print(f"Copied {src} -> {dst}")
            break

    candidates_csv = [
        ROOT / "data" / "movies" / "movies.csv",
        ROOT / "data" / "movies.csv",
    ]
    for src in candidates_csv:
        if src.exists():
            dst = outdir / "movies.csv"
            shutil.copy2(src, dst)
            print(f"Copied {src} -> {dst}")
            break

    # If no JSON present, create a minimal sample file so repo has something
    if not (outdir / "movies.json").exists() and not (outdir / "movies.csv").exists():
        sample = [
            {
                "movie_id": "sample1",
                "title": "Sample Movie",
                "movieGenres": "Drama",
                "datePublished": "2020-01-01",
                "rating": 7.1,
                "created_at": datetime.utcnow().isoformat() + "Z",
                "updated_at": datetime.utcnow().isoformat() + "Z",
            }
        ]
        with (outdir / "movies.json").open("w", encoding="utf-8") as f:
            json.dump(sample, f, ensure_ascii=False, indent=2)
        print(f"Wrote sample JSON to {outdir / 'movies.json'}")

    return outdir


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--outdir", type=Path, default=DEFAULT_OUT, help="Test output directory"
    )
    args = parser.parse_args(argv)

    outdir = prepare_test_dir(args.outdir)

    # Set environment variables BEFORE importing the repository module
    os.environ["MOVIES_JSON_PATH"] = str(outdir / "movies.json")
    os.environ["MOVIES_CSV_PATH"] = str(outdir / "movies.csv")

    print("Using test data directory:", outdir)

    # Import repo after env vars are set (module reads env at import time)
    from backend.repositories.movies_repo import MovieRepository
    from backend.schemas.movies import MovieCreate

    # Use CSV-backed repo if CSV file exists, else JSON
    use_json = not (outdir / "movies.csv").exists()
    repo = MovieRepository(use_json=use_json)

    print("Initial movie count:", repo.get_all()[1])
    items, total = repo.get_all()
    if items:
        print("First movie:", items[0].title, "(id=", items[0].movie_id, ")")

    # Create a test movie
    print("Creating a test movie...")
    # Create a test movie using fields aligned with `MovieBase` schema
    new = repo.create(
        MovieCreate(
            title="Workflow Test Movie", movieGenres="Test", datePublished="2025-01-01"
        )
    )
    print("Created movie id:", new.movie_id)

    # Force reload by clearing internal cache (safe for testing)
    try:
        repo._cache = None
    except Exception:
        pass

    print("After create, movie count:", repo.get_all()[1])

    # Delete the created movie
    print("Deleting the test movie...")
    deleted = repo.delete(new.movie_id)
    print("Deleted?", deleted)

    # Final count
    repo._cache = None
    print("Final movie count:", repo.get_all()[1])

    print("Test data written under:", outdir)
    print(
        "Note: this script modifies only the test directory; your original data is left untouched."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
