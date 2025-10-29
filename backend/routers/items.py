from fastapi import APIRouter
from utils.data_loader import load_all_data

router = APIRouter(prefix="/data", tags=["data"])

@router.get("/")
def get_all_data():
    data = load_all_data()
    return data