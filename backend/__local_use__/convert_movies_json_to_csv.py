#!/usr/bin/env python3
"""Convert `backend/data/movies.json` to `backend/data/movies.csv`.

This script joins list fields with '|' and writes a CSV with a stable header.
Run from repository root:

    python backend/__local_use__/convert_movies_json_to_csv.py

"""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, List

SRC = Path(__file__).resolve().parents[1] / "data" / "movies.json"
OUT = Path(__file__).resolve().parents[1] / "data" / "movies.csv"


def join_list(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return "|".join(str(v) for v in value)
    return str(value)


def normalize_row(m: Dict[str, Any]) -> Dict[str, str]:
    return {
        "title": str(m.get("title", "")),
        "movieIMDbRating": str(m.get("movieIMDbRating", "")),
        "totalRatingCount": str(m.get("totalRatingCount", "")),
        "totalUserReviews": str(m.get("totalUserReviews", "")),
        "totalCriticReviews": str(m.get("totalCriticReviews", "")),
        "metaScore": str(m.get("metaScore", "")),
        "movieGenres": join_list(m.get("movieGenres")),
        "directors": join_list(m.get("directors")),
        "datePublished": str(m.get("datePublished", "")),
        "creators": join_list(m.get("creators")),
        "mainStars": join_list(m.get("mainStars")),
        "description": str(m.get("description", "")),
        "duration": str(m.get("duration", "")),
        "movie_id": str(m.get("movie_id", "")),
    }


def main() -> None:
    if not SRC.exists():
        raise SystemExit(f"Source JSON not found: {SRC}")

    with SRC.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise SystemExit("Expected a JSON array in movies.json")

    rows: List[Dict[str, str]] = [normalize_row(m) for m in data]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "title",
                "movieIMDbRating",
                "totalRatingCount",
                "totalUserReviews",
                "totalCriticReviews",
                "metaScore",
                "movieGenres",
                "directors",
                "datePublished",
                "creators",
                "mainStars",
                "description",
                "duration",
                "movie_id",
            ],
            quoting=csv.QUOTE_MINIMAL,
        )
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


if __name__ == "__main__":
    main()
