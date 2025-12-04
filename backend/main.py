"""
Main FastAPI application entrypoint.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import admin_analytics, admin_sync, auth, history, password_reset
from backend.routers.bookmarks import router as bookmarks_router
from backend.routers.lists import router as lists_router
from backend.routers.movies import router as movies_router
from backend.routers.penalties import router as penalties_router
from backend.routers.recommendations import router as recommendations_router
from backend.routers.reviews import router as reviews_router
from backend.routers.users import router as users_router

app = FastAPI()

# Allow CORS from local frontend dev servers (Vite)
# Include both localhost and 127.0.0.1 variants in case Vite uses either.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    """Return a simple status message to indicate the API is running."""
    return {"status": "ok"}


# Admin routers
app.include_router(admin_analytics.router)
app.include_router(admin_sync.router)

# Reviews router
app.include_router(reviews_router)

# Recommendations router
app.include_router(recommendations_router)
# Password reset router
app.include_router(password_reset.router)

# Auth router (token endpoint)
app.include_router(auth.router)

# Users router
app.include_router(users_router)

# Bookmarks router
app.include_router(bookmarks_router)

# Movies router
app.include_router(movies_router)

# Penalties router
app.include_router(penalties_router)

# History router
app.include_router(history.router)

# Lists router
app.include_router(lists_router)
