import os
import sys
from datetime import datetime

from backend.repositories.reviews_repo import DATE_INPUT_FORMATS, _parse_date

# Add project root to sys.path
sys.path.append(os.getcwd())


def test_date_parsing():
    test_dates = [
        "27 October 2025",
        "15 Jan 24",
        "2023-12-25",
        "2024-01-01T12:00:00Z",  # ISO format
    ]

    print(f"Testing date parsing with formats: {DATE_INPUT_FORMATS}")

    for date_str in test_dates:
        parsed = _parse_date(date_str)
        print(f"Input: '{date_str}' -> Parsed: {parsed}")

        # Check if it defaulted to now (approximate check)
        now = datetime.now().timestamp()
        if abs(parsed.timestamp() - now) < 5:  # within 5 seconds
            print(
                f"  WARNING: '{date_str}' likely failed to parse and defaulted to NOW"
            )
        else:
            print(f"  SUCCESS: '{date_str}' parsed correctly")


if __name__ == "__main__":
    test_date_parsing()
