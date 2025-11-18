"""
Main FastAPI application entrypoint.
"""

from fastapi import FastAPI
from routers import admin_analytics, admin_sync
from routers.recommendations import router as recommendations_router
from routers.reviews import router as reviews_router

app = FastAPI()


@app.get("/health")
def health() -> dict[str, str]:
    """Return a simple status message to indicate the API is running."""
    return {"status": "ok"}


# Admin routers
app.include_router(admin_analytics.router)
app.include_router(admin_sync.router)

# Reviews router (demo)
app.include_router(reviews_router)

# Recommendations router
app.include_router(recommendations_router)
