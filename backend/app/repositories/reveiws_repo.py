from __future__ import annotations
import csv
import os
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

# Base directory for data files
BASE_PATH = os.getenv("MOVIE_DATA_PATH", "data/movies")
