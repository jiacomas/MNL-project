from pydantic import BaseModel
from typing import List

class Movies(BaseModel):
    title : str
    category:str
    tags: List[str] = []

class Bookmark(BaseModel):
    id: str
    movies: List[str] = []