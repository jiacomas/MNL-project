from fastapi import FastAPI
from .routers.password_reset import router as password_reset_router

app = FastAPI(title="MNL Password Reset API")

# Routers
app.include_router(password_reset_router)

# Health (optional)
@app.get("/health")
def health():
    return {"ok": True}
