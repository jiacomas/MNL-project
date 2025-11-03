from fastapi import FastAPI
from backend.app.routers import movies

app = FastAPI(title="IMDB Movies User Reviews API", version="1.0.0")

# Include routers
app.include_router(movies.router)

@app.get("/")
async def root():
    return {"message": "IMDB Movies User Reviews API"}


@app.get("/health")
async def health_check():
    return {"status": "ok"}