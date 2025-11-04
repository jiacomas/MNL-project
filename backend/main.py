"""
Main FastAPI application entrypoint.
Includes health check endpoint and item router.
"""

from fastapi import FastAPI
from routers.items import router as items_router
from backend.routers import admin_analytics, admin_sync

app = FastAPI()


@app.get("/health")
def health():
    """Return a simple status message to indicate the API is running."""
    return {"status": "ok"}

app.include_router(admin_analytics.router)
app.include_router(admin_sync.router)
# Don't do this in production; just for demo purposes
app.include_router(items_router)
