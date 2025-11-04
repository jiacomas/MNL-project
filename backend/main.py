"""
Main FastAPI application entrypoint.
"""

from fastapi import FastAPI
from routers.reviews import router as reviews_router

app = FastAPI()


@app.get("/health")
def health():
    """Return a simple status message to indicate the API is running."""
    return {"status": "ok"}


# Don't do this in production; just for demo purposes
app.include_router(reviews_router)
