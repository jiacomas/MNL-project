from fastapi import FastAPI
# from app.routers.items import router as items_router
from app.routers.reviews import router as reviews_router

app = FastAPI(title="MNL Project")
app.include_router(reviews_router)

@app.get("/health")
def health():
    return {"status": "ok"}

## don't do this, just for demo purposes

# app.include_router(items_router)
