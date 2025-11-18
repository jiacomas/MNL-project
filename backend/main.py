"""
Main FastAPI application entrypoint.
"""

from fastapi import FastAPI

from backend.routers import admin_analytics, admin_sync, password_reset
from backend.routers.bookmarks import router as bookmarks_router
from backend.routers.reviews import router as reviews_router

app = FastAPI()


@app.get("/health")
def health() -> dict[str, str]:
    """Return a simple status message to indicate the API is running."""
    return {"status": "ok"}


# Admin routers
app.include_router(admin_analytics.router)
app.include_router(admin_sync.router)

# Reviews router
app.include_router(reviews_router)

# Password reset router
app.include_router(password_reset.router)

# Bookmarks router
app.include_router(bookmarks_router)
