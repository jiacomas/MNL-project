# Reviews service
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from fastapi import HTTPException

from app.schemas.reviews import ReviewCreate, ReviewUpdate, ReviewOut
from app.repositories.reviews_repo import load_all, save_all

#TODO: Implement database-backed repository later